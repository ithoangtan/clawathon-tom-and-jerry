import type { I18nKey } from "./i18n";

export type TutorialRoute = "/" | "/dashboard" | "/settings";

export type TutorialStepId =
  | "welcome"
  | "departments"
  | "examples"
  | "chat-input"
  | "citations"
  | "nav-dashboard"
  | "dashboard-overview"
  | "finish";

export interface TutorialStepDefinition {
  id: TutorialStepId;
  target?: string;
  route: TutorialRoute;
  titleKey: I18nKey;
  descriptionKey: I18nKey;
  side?: "top" | "right" | "bottom" | "left" | "over";
  align?: "start" | "center" | "end";
  navigateOnNext?: TutorialRoute;
}

export const TUTORIAL_STEPS: TutorialStepDefinition[] = [
  {
    id: "welcome",
    route: "/",
    titleKey: "tutorial.welcome.title",
    descriptionKey: "tutorial.welcome.description",
    side: "over",
    align: "center",
  },
  {
    id: "departments",
    target: '[data-tour="department-bar"]',
    route: "/",
    titleKey: "tutorial.departments.title",
    descriptionKey: "tutorial.departments.description",
    side: "bottom",
    align: "start",
  },
  {
    id: "examples",
    target: '[data-tour="example-questions"]',
    route: "/",
    titleKey: "tutorial.examples.title",
    descriptionKey: "tutorial.examples.description",
    side: "top",
    align: "center",
  },
  {
    id: "chat-input",
    target: '[data-tour="chat-input"]',
    route: "/",
    titleKey: "tutorial.chatInput.title",
    descriptionKey: "tutorial.chatInput.description",
    side: "top",
    align: "center",
  },
  {
    id: "citations",
    route: "/",
    titleKey: "tutorial.citations.title",
    descriptionKey: "tutorial.citations.description",
    side: "over",
    align: "center",
  },
  {
    id: "nav-dashboard",
    target: '[data-tour="nav-dashboard"]',
    route: "/",
    titleKey: "tutorial.navDashboard.title",
    descriptionKey: "tutorial.navDashboard.description",
    side: "bottom",
    align: "start",
    navigateOnNext: "/dashboard",
  },
  {
    id: "dashboard-overview",
    target: '[data-tour="dashboard-overview"]',
    route: "/dashboard",
    titleKey: "tutorial.dashboardOverview.title",
    descriptionKey: "tutorial.dashboardOverview.description",
    side: "bottom",
    align: "start",
    navigateOnNext: "/",
  },
  {
    id: "finish",
    target: '[data-tour="tutorial-help"]',
    route: "/",
    titleKey: "tutorial.finish.title",
    descriptionKey: "tutorial.finish.description",
    side: "bottom",
    align: "end",
  },
];
