import { classNames } from "@/lib/format";
import { forwardRef, type HTMLAttributes } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  padding?: "sm" | "md" | "lg";
}

const paddingMap = {
  sm: "p-4",
  md: "p-5",
  lg: "p-6",
};

export const Card = forwardRef<HTMLDivElement, CardProps>(function Card(
  { padding = "md", className, children, ...props },
  ref,
) {
  return (
    <div
      ref={ref}
      className={classNames(
        "surface-card shadow-glass",
        paddingMap[padding],
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
});
