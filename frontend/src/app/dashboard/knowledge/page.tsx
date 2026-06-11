import { auth } from "@clerk/nextjs/server";
import { createAnonClient } from "@/lib/supabase/client";
import { redirect } from "next/navigation";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import UploadDocumentModal from "@/components/UploadDocumentModal";

interface DocumentRow {
  id: string;
  filename: string;
  chunks_ingested: number;
  created_at: string;
}

export default async function KnowledgeBasePage() {
  const { userId } = await auth();
  if (!userId) redirect("/sign-in");

  const supabase = createAnonClient();

  const { data: documents, error } = await supabase
    .from("documents")
    .select("id, filename, chunks_ingested, created_at, users!inner(clerk_id)")
    .eq("users.clerk_id", userId)
    .order("created_at", { ascending: false });

  if (error) {
    console.error("Documents query error:", error.message);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">
            Knowledge Base
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Uploaded documents used as context for ticket triage.
          </p>
        </div>
        <UploadDocumentModal />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">
            Uploaded Documents
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!documents || documents.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">
              No documents uploaded yet. Upload a PDF to add context for the
              triage agent.
            </p>
          ) : (
            <ul className="space-y-2">
              {(documents as DocumentRow[]).map((doc) => (
                <li
                  key={doc.id}
                  className="flex items-center justify-between rounded-md border border-slate-200 px-3 py-2"
                >
                  <span className="text-sm font-medium text-slate-700 truncate">
                    {doc.filename}
                  </span>
                  <span className="text-xs text-slate-500">
                    {doc.chunks_ingested} chunks · {new Date(doc.created_at).toLocaleDateString()}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}