"use client";

import { useState, useRef } from "react";
import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { UploadIcon, FileIcon, LoaderCircleIcon } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

export default function UploadDocumentModal() {
  const { getToken } = useAuth();
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [open, setOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setMessage(null);

    try {
      const token = await getToken();
      const formData = new FormData();
      formData.append("file", file);

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8080";
      const res = await fetch(`${apiUrl}/api/v1/documents`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(err.detail || "Upload failed");
      }

      const data = await res.json();
      setMessage({
        type: "success",
        text: `"${data.filename}" uploaded — ${data.chunks_ingested} chunks ingested.`,
      });
      router.refresh();
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (err) {
      setMessage({
        type: "error",
        text: err instanceof Error ? err.message : "An unexpected error occurred.",
      });
    } finally {
      setUploading(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        render={
          <Button variant="outline" size="sm">
            <UploadIcon className="size-4" />
            Upload Document
          </Button>
        }
      />
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Upload PDF Document</DialogTitle>
          <DialogDescription>
            Upload a PDF to ingest into the knowledge base for RAG-powered
            triage.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="grid gap-4">
          <div className="grid gap-2">
            <Label htmlFor="file-upload">PDF File</Label>
            <div className="flex items-center gap-2">
              <input
                ref={fileInputRef}
                id="file-upload"
                type="file"
                accept="application/pdf"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="block w-full text-sm text-slate-500
                  file:mr-2 file:rounded-md file:border-0
                  file:bg-slate-100 file:px-3 file:py-1.5
                  file:text-sm file:font-medium file:text-slate-700
                  hover:file:bg-slate-200"
              />
            </div>
            {file && (
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                <FileIcon className="size-3" />
                {file.name} ({(file.size / 1024).toFixed(1)} KB)
              </p>
            )}
          </div>

          {message && (
            <p
              className={`text-sm rounded-md px-3 py-2 ${
                message.type === "success"
                  ? "bg-emerald-50 text-emerald-700"
                  : "bg-red-50 text-red-700"
              }`}
            >
              {message.text}
            </p>
          )}

          <DialogFooter>
            <DialogClose render={<Button variant="outline" />}>
              Cancel
            </DialogClose>
            <Button type="submit" disabled={!file || uploading}>
              {uploading ? (
                <LoaderCircleIcon className="size-4 animate-spin" />
              ) : (
                <UploadIcon className="size-4" />
              )}
              {uploading ? "Uploading…" : "Upload"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}