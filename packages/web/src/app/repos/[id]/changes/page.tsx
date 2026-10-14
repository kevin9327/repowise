import { redirect } from "next/navigation";
import { commitsViewHref } from "@/lib/changes";

/** The change list lives on the Commits page, grouped by change. */
export default async function ChangesPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  redirect(commitsViewHref(id, "changes"));
}
