import { TUTORIAL_STEPS_BY_KEY } from "@/lib/onboarding";
import type { TutorialKey, TutorialStepDefinition, TutorialRoute } from "@/lib/onboarding";
import { t } from "@/lib/i18n";
import type { Lang } from "@/lib/types";
import { useTutorialStore } from "@/store/tutorialStore";
import { useUserStore } from "@/store/userStore";
import { driver, type DriveStep, type Driver } from "driver.js";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useLocation, useNavigate } from "react-router-dom";

const NAV_WAIT_MS = 80;

function normalizePathToTutorialRoute(pathname: string): TutorialRoute {
  if (pathname === "/" || pathname.startsWith("/chat/")) return "/";
  if (pathname.startsWith("/dashboard")) return "/dashboard";
  if (pathname.startsWith("/settings")) return "/settings";
  if (pathname.startsWith("/admin")) return "/admin";
  return "/";
}

export function pathToTutorialKey(pathname: string): TutorialKey {
  if (pathname.startsWith("/dashboard")) return "dashboard";
  if (pathname.startsWith("/settings")) return "settings";
  if (pathname.startsWith("/admin")) return "admin";
  return "chat";
}

interface TutorialContextValue {
  startTutorial: (key: TutorialKey, fromStep?: number) => void;
  pauseTutorial: () => void;
  isRunning: boolean;
  activeKey: TutorialKey | null;
}

const TutorialContext = createContext<TutorialContextValue | null>(null);

function waitForElement(selector: string, timeoutMs = 4000): Promise<Element | null> {
  const existing = document.querySelector(selector);
  if (existing) return Promise.resolve(existing);

  return new Promise((resolve) => {
    const deadline = Date.now() + timeoutMs;
    const observer = new MutationObserver(() => {
      const el = document.querySelector(selector);
      if (el) {
        observer.disconnect();
        resolve(el);
      } else if (Date.now() > deadline) {
        observer.disconnect();
        resolve(null);
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
    setTimeout(() => {
      observer.disconnect();
      resolve(document.querySelector(selector));
    }, timeoutMs);
  });
}

function injectDismissFooter(
  footer: HTMLElement,
  dismissLabel: string,
  getDismiss: () => boolean,
  onDismissChange: (dismiss: boolean) => void,
) {
  let row = footer.querySelector<HTMLElement>('[data-tutorial-dismiss-row="true"]');
  if (!row) {
    row = document.createElement("div");
    row.dataset.tutorialDismissRow = "true";
    row.className = "zp-tutorial-dismiss";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.id = "tutorial-dismiss-checkbox";
    checkbox.checked = getDismiss();
    checkbox.addEventListener("change", () => {
      onDismissChange(checkbox.checked);
    });

    const label = document.createElement("label");
    label.htmlFor = checkbox.id;
    label.textContent = dismissLabel;

    row.append(checkbox, label);
    footer.insertBefore(row, footer.firstChild);
  } else {
    const checkbox = row.querySelector("input");
    if (checkbox instanceof HTMLInputElement) {
      checkbox.checked = getDismiss();
    }
  }
}

function buildDriveSteps(
  steps: TutorialStepDefinition[],
  locale: Lang,
  handlers: {
    onNavigate: (route: TutorialRoute) => Promise<void>;
    onDismissChange: (dismiss: boolean) => void;
    getDismiss: () => boolean;
  },
): DriveStep[] {
  const dismissLabel = t("tutorialDismiss", locale);
  const doneLabel = t("tutorialDone", locale);

  return steps.map((step, index) => {
    const driveStep: DriveStep = {
      popover: {
        title: t(step.titleKey, locale),
        description: t(step.descriptionKey, locale),
        side: step.side ?? "bottom",
        align: step.align ?? "start",
        showButtons: ["previous", "next", "close"],
        popoverClass: "zp-tutorial-popover",
        onPopoverRender: (popover, { state }) => {
          injectDismissFooter(
            popover.footer,
            dismissLabel,
            handlers.getDismiss,
            handlers.onDismissChange,
          );
          if (index === steps.length - 1) {
            popover.nextButton.textContent = doneLabel;
          }
          if (popover.progress) {
            const current = (state.activeIndex ?? index) + 1;
            popover.progress.textContent = t("tutorialProgress", locale, {
              current,
              total: steps.length,
            });
          }
        },
        onNextClick: async (_element, _step, { driver: tour }) => {
          if (step.navigateOnNext) {
            await handlers.onNavigate(step.navigateOnNext);
            const nextTarget = steps[index + 1]?.target;
            if (nextTarget) await waitForElement(nextTarget);
            tour.moveNext();
            return;
          }
          if (index === steps.length - 1) {
            tour.destroy();
            return;
          }
          tour.moveNext();
        },
        onCloseClick: (_element, _step, { driver: tour }) => {
          tour.destroy();
        },
      },
    };

    if (step.target) {
      driveStep.element = step.target;
    }

    driveStep.onHighlightStarted = async (_el, _step, { driver: tour }) => {
      if (normalizePathToTutorialRoute(window.location.pathname) !== step.route) {
        await handlers.onNavigate(step.route);
      }
      if (step.target) {
        await waitForElement(step.target);
        tour.refresh();
      }
    };

    return driveStep;
  });
}

function useTutorialController() {
  const navigate = useNavigate();
  const location = useLocation();
  const locale = useUserStore((s) => s.locale);
  const setDismissed = useTutorialStore((s) => s.setDismissed);
  const hasHydrated = useTutorialStore((s) => s.hasHydrated);
  const driverRef = useRef<Driver | null>(null);
  const dismissPendingRef = useRef(false);
  const activeKeyRef = useRef<TutorialKey | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [activeKey, setActiveKey] = useState<TutorialKey | null>(null);

  const navigateForTour = useCallback(
    async (route: TutorialRoute) => {
      if (normalizePathToTutorialRoute(location.pathname) === route) return;
      navigate(route);
      await new Promise((resolve) => setTimeout(resolve, NAV_WAIT_MS));
    },
    [location.pathname, navigate],
  );

  const destroyTour = useCallback(() => {
    driverRef.current?.destroy();
    driverRef.current = null;
    setIsRunning(false);
    setActiveKey(null);
    activeKeyRef.current = null;
  }, []);

  const startTutorial = useCallback(
    (key: TutorialKey, fromStep = 0) => {
      destroyTour();
      dismissPendingRef.current = false;
      activeKeyRef.current = key;

      const steps = TUTORIAL_STEPS_BY_KEY[key];

      const tour = driver({
        animate: true,
        overlayColor: "#060a12",
        overlayOpacity: 0.72,
        stagePadding: 10,
        stageRadius: 14,
        smoothScroll: true,
        allowClose: true,
        showProgress: true,
        nextBtnText: t("tutorialNext", locale),
        prevBtnText: t("tutorialBack", locale),
        doneBtnText: t("tutorialDone", locale),
        popoverClass: "zp-tutorial-popover",
        steps: buildDriveSteps(steps, locale, {
          onNavigate: navigateForTour,
          onDismissChange: (dismiss) => {
            dismissPendingRef.current = dismiss;
          },
          getDismiss: () => dismissPendingRef.current,
        }),
        onDestroyed: () => {
          if (dismissPendingRef.current && activeKeyRef.current) {
            setDismissed(activeKeyRef.current, true);
          }
          driverRef.current = null;
          setIsRunning(false);
          setActiveKey(null);
          activeKeyRef.current = null;
        },
      });

      driverRef.current = tour;
      setIsRunning(true);
      setActiveKey(key);

      if (key === "chat" && fromStep === 0) {
        const { newSession } = useUserStore.getState();
        newSession();
        const freshSessionId = useUserStore.getState().sessionId;
        navigate(`/chat/${freshSessionId}`);
        void waitForElement('[data-tour="chat-input"]').then(() => tour.drive(0));
        return;
      }

      const firstStep = steps[fromStep];
      if (firstStep && normalizePathToTutorialRoute(location.pathname) !== firstStep.route) {
        void navigateForTour(firstStep.route).then(() => tour.drive(fromStep));
        return;
      }

      tour.drive(fromStep);
    },
    [destroyTour, locale, location.pathname, navigate, navigateForTour, setDismissed],
  );

  useEffect(() => () => destroyTour(), [destroyTour]);

  // Auto-start chat tutorial on first visit
  const chatDismissed = useTutorialStore((s) => s.dismissed["chat"] ?? false);
  const autoStartedRef = useRef(false);

  useEffect(() => {
    if (!hasHydrated || chatDismissed || autoStartedRef.current || isRunning) return;
    if (normalizePathToTutorialRoute(location.pathname) !== "/") return;
    const timerId = window.setTimeout(() => {
      autoStartedRef.current = true;
      startTutorial("chat", 0);
    }, 3000);
    return () => window.clearTimeout(timerId);
  }, [hasHydrated, chatDismissed, isRunning, startTutorial, location.pathname]);

  const pauseTutorial = useCallback(() => {
    destroyTour();
  }, [destroyTour]);

  return { startTutorial, pauseTutorial, isRunning, activeKey };
}

export function TutorialProvider({ children }: { children: ReactNode }) {
  const { startTutorial, pauseTutorial, isRunning, activeKey } = useTutorialController();
  return (
    <TutorialContext.Provider value={{ startTutorial, pauseTutorial, isRunning, activeKey }}>
      {children}
    </TutorialContext.Provider>
  );
}

export function useTutorialContext(): TutorialContextValue {
  const ctx = useContext(TutorialContext);
  if (!ctx) {
    throw new Error("useTutorialContext must be used within TutorialProvider");
  }
  return ctx;
}

/** Hook for page-level auto-show. Call once at the top of a page component. */
export function usePageTutorial(key: TutorialKey, delayMs = 1500) {
  const { startTutorial, isRunning, activeKey } = useTutorialContext();
  const isDismissed = useTutorialStore((s) => s.dismissed[key] ?? false);
  const hasHydrated = useTutorialStore((s) => s.hasHydrated);
  const autoStartedRef = useRef(false);

  useEffect(() => {
    if (!hasHydrated || isDismissed || autoStartedRef.current || isRunning) return;
    const timer = window.setTimeout(() => {
      autoStartedRef.current = true;
      startTutorial(key, 0);
    }, delayMs);
    return () => window.clearTimeout(timer);
  }, [hasHydrated, isDismissed, isRunning, startTutorial, key, delayMs]);

  return {
    startTutorial: () => startTutorial(key, 0),
    isRunning: isRunning && activeKey === key,
  };
}

/** Safe outside TutorialProvider — used by department picker to pause an active tour. */
export function useTutorialPauseOptional(): Pick<TutorialContextValue, "pauseTutorial" | "isRunning"> {
  const ctx = useContext(TutorialContext);
  return {
    pauseTutorial: ctx?.pauseTutorial ?? (() => {}),
    isRunning: ctx?.isRunning ?? false,
  };
}
