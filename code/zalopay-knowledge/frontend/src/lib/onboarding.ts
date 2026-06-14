import type { I18nKey } from "./i18n";
import type { TutorialKey } from "@/store/tutorialStore";

export type { TutorialKey };

export type TutorialRoute = "/" | "/dashboard" | "/settings" | "/admin";

export type TutorialStepId =
  | "welcome"
  | "departments"
  | "examples"
  | "chat-input"
  | "chat-finish"
  | "response-welcome"
  | "response-answer"
  | "response-citations"
  | "response-feedback"
  | "dashboard-welcome"
  | "dashboard-metrics"
  | "dashboard-history"
  | "settings-welcome"
  | "settings-identity"
  | "settings-sync"
  | "admin-welcome"
  | "admin-cards"
  | "admin-sources"
  | "admin-jobs";

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

export const CHAT_TUTORIAL_STEPS: TutorialStepDefinition[] = [
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
    id: "chat-finish",
    target: '[data-tour="tutorial-help"]',
    route: "/",
    titleKey: "tutorial.finish.title",
    descriptionKey: "tutorial.finish.description",
    side: "bottom",
    align: "end",
  },
];

export const RESPONSE_TUTORIAL_STEPS: TutorialStepDefinition[] = [
  {
    id: "response-welcome",
    route: "/",
    titleKey: "tutorial.response.welcome.title",
    descriptionKey: "tutorial.response.welcome.description",
    side: "over",
    align: "center",
  },
  {
    id: "response-answer",
    target: '[data-tour="response-answer"]',
    route: "/",
    titleKey: "tutorial.response.answer.title",
    descriptionKey: "tutorial.response.answer.description",
    side: "bottom",
    align: "start",
  },
  {
    id: "response-citations",
    target: '[data-tour="response-citations"]',
    route: "/",
    titleKey: "tutorial.response.citations.title",
    descriptionKey: "tutorial.response.citations.description",
    side: "top",
    align: "start",
  },
  {
    id: "response-feedback",
    target: '[data-tour="response-feedback"]',
    route: "/",
    titleKey: "tutorial.response.feedback.title",
    descriptionKey: "tutorial.response.feedback.description",
    side: "top",
    align: "start",
  },
];

export const DASHBOARD_TUTORIAL_STEPS: TutorialStepDefinition[] = [
  {
    id: "dashboard-welcome",
    route: "/dashboard",
    titleKey: "tutorial.dashboard.welcome.title",
    descriptionKey: "tutorial.dashboard.welcome.description",
    side: "over",
    align: "center",
  },
  {
    id: "dashboard-metrics",
    target: '[data-tour="dashboard-metrics"]',
    route: "/dashboard",
    titleKey: "tutorial.dashboard.metrics.title",
    descriptionKey: "tutorial.dashboard.metrics.description",
    side: "bottom",
    align: "start",
  },
  {
    id: "dashboard-history",
    target: '[data-tour="dashboard-history"]',
    route: "/dashboard",
    titleKey: "tutorial.dashboard.history.title",
    descriptionKey: "tutorial.dashboard.history.description",
    side: "top",
    align: "start",
  },
];

export const SETTINGS_TUTORIAL_STEPS: TutorialStepDefinition[] = [
  {
    id: "settings-welcome",
    route: "/settings",
    titleKey: "tutorial.settings.welcome.title",
    descriptionKey: "tutorial.settings.welcome.description",
    side: "over",
    align: "center",
  },
  {
    id: "settings-identity",
    target: '[data-tour="settings-identity"]',
    route: "/settings",
    titleKey: "tutorial.settings.identity.title",
    descriptionKey: "tutorial.settings.identity.description",
    side: "bottom",
    align: "start",
  },
  {
    id: "settings-sync",
    target: '[data-tour="settings-sync"]',
    route: "/settings",
    titleKey: "tutorial.settings.sync.title",
    descriptionKey: "tutorial.settings.sync.description",
    side: "top",
    align: "start",
  },
];

export const ADMIN_TUTORIAL_STEPS: TutorialStepDefinition[] = [
  {
    id: "admin-welcome",
    route: "/admin",
    titleKey: "tutorial.admin.welcome.title",
    descriptionKey: "tutorial.admin.welcome.description",
    side: "over",
    align: "center",
  },
  {
    id: "admin-cards",
    target: '[data-tour="admin-cards"]',
    route: "/admin",
    titleKey: "tutorial.admin.cards.title",
    descriptionKey: "tutorial.admin.cards.description",
    side: "bottom",
    align: "start",
  },
  {
    id: "admin-sources",
    target: '[data-tour="admin-sources"]',
    route: "/admin",
    titleKey: "tutorial.admin.sources.title",
    descriptionKey: "tutorial.admin.sources.description",
    side: "top",
    align: "start",
  },
  {
    id: "admin-jobs",
    target: '[data-tour="admin-jobs"]',
    route: "/admin",
    titleKey: "tutorial.admin.jobs.title",
    descriptionKey: "tutorial.admin.jobs.description",
    side: "top",
    align: "start",
  },
];

export const TUTORIAL_STEPS_BY_KEY: Record<TutorialKey, TutorialStepDefinition[]> = {
  chat: CHAT_TUTORIAL_STEPS,
  response: RESPONSE_TUTORIAL_STEPS,
  dashboard: DASHBOARD_TUTORIAL_STEPS,
  settings: SETTINGS_TUTORIAL_STEPS,
  admin: ADMIN_TUTORIAL_STEPS,
};

export const TUTORIAL_ROUTE_BY_KEY: Record<TutorialKey, TutorialRoute> = {
  chat: "/",
  response: "/",
  dashboard: "/dashboard",
  settings: "/settings",
  admin: "/admin",
};
