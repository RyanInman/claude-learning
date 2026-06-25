import { theme } from "../theme";

export function Modal({ children }: { children: React.ReactNode }) {
  return <div style={{ background: theme.surface }}>{children}</div>;
}
