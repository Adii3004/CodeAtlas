import {
  FileBarChart,
  FolderGit2,
  LayoutDashboard,
  MessagesSquare,
  Network,
  Settings,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  title: string;
  to: string;
  icon: LucideIcon;
  description: string;
  /** Match only the exact path (used for the index route). */
  end?: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  {
    title: "Overview",
    to: "/",
    icon: LayoutDashboard,
    description: "Service health and everything you have mapped so far",
    end: true,
  },
  {
    title: "Repositories",
    to: "/repositories",
    icon: FolderGit2,
    description: "Scan a codebase, then index it for questions",
  },
  {
    title: "Ask CodeAtlas",
    to: "/chat",
    icon: MessagesSquare,
    description: "Grounded answers about your indexed repository",
  },
  {
    title: "Dependency Map",
    to: "/graph",
    icon: Network,
    description: "How every file connects to the rest",
  },
  {
    title: "Insights",
    to: "/report",
    icon: FileBarChart,
    description: "Architecture metrics, rankings, and issues",
  },
  {
    title: "Settings",
    to: "/settings",
    icon: Settings,
    description: "Connection, appearance, and answer defaults",
  },
];
