import { Separator } from "react-resizable-panels";
import { classNames } from "@/lib/format";

export function SidebarResizeHandle({ className }: { className?: string }) {
  return (
    <Separator
      className={classNames(
        "group relative w-1 cursor-col-resize bg-border transition-colors duration-150",
        "hover:bg-brand/30 active:bg-brand/50",
        className,
      )}
    >
      <div className="absolute inset-y-0 left-1/2 flex -translate-x-1/2 flex-col items-center justify-center gap-[3px] opacity-0 transition-opacity duration-150 group-hover:opacity-100 group-active:opacity-100">
        <span className="h-1 w-1 rounded-full bg-brand" />
        <span className="h-1 w-1 rounded-full bg-brand" />
        <span className="h-1 w-1 rounded-full bg-brand" />
      </div>
    </Separator>
  );
}
