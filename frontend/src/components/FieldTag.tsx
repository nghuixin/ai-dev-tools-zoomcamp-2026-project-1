type Props = {
  state?: "ai" | "edited";
};

export function FieldTag({ state }: Props) {
  if (!state) return null;
  return <span className={`field-tag field-tag-${state}`}>{state === "ai" ? "AI" : "EDITED"}</span>;
}
