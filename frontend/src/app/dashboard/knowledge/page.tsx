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

interface StoredFile {
  id: string;
  name: string;
  created_at: string;
  metadata: Record<string, unknown>;
}

export default async function KnowledgeBasePage() {
  const { userId } = await auth();
  if (!userId) redirect("/sign-in");

  const supabase = createAnonClient();

  const { data: files, error } = await supabase.storage
    .from("raw_documents")
    .list(userId, {
      limit: 100,
      sortBy: { column: "created_at", order: "desc" },
    });

  if (error) {
    console.error("Storage list error:", error.message);
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
          {!files || files.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">
              No documents uploaded yet. Upload a PDF to add context for the
              triage agent.
            </p>
          ) : (
            <ul className="space-y-2">
              {(files as StoredFile[]).map((file) => (
                <li
                  key={file.id}
                  className="flex items-center justify-between rounded-md border border-slate-200 px-3 py-2"
                >
                  <span className="text-sm font-medium text-slate-700 truncate">
                    {file.name}
                  </span>
                  <span className="text-xs text-slate-500">
                    {new Date(file.created_at).toLocaleDateString()}
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