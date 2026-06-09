import { NextRequest, NextResponse } from "next/server";
import { Webhook } from "svix";
import { createAnonClient } from "@/lib/supabase/client";

interface ClerkEmailAddress {
  id: string;
  email_address: string;
}

interface ClerkUserCreatedEvent {
  data: {
    id: string;
    email_addresses: ClerkEmailAddress[];
    primary_email_address_id: string;
  };
  type: string;
}

export async function POST(req: NextRequest): Promise<NextResponse> {
  const payload = await req.text();

  const svixId = req.headers.get("svix-id");
  const svixTimestamp = req.headers.get("svix-timestamp");
  const svixSignature = req.headers.get("svix-signature");

  if (!svixId || !svixTimestamp || !svixSignature) {
    return NextResponse.json(
      { error: "Missing svix headers" },
      { status: 400 },
    );
  }

  const webhookSecret = process.env.WEBHOOK_SECRET;
  if (!webhookSecret) {
    console.error("WEBHOOK_SECRET is not configured");
    return NextResponse.json(
      { error: "Webhook secret not configured" },
      { status: 500 },
    );
  }

  let evt: ClerkUserCreatedEvent;

  try {
    const wh = new Webhook(webhookSecret);
    evt = wh.verify(payload, {
      "svix-id": svixId,
      "svix-timestamp": svixTimestamp,
      "svix-signature": svixSignature,
    }) as ClerkUserCreatedEvent;
  } catch (err) {
    console.error("Webhook signature verification failed:", err);
    return NextResponse.json(
      { error: "Invalid webhook signature" },
      { status: 400 },
    );
  }

  if (evt.type !== "user.created") {
    return NextResponse.json({ message: `Ignored event type: ${evt.type}` });
  }

  const { id: clerkId, email_addresses, primary_email_address_id } = evt.data;

  const primaryEmail = email_addresses.find(
    (e) => e.id === primary_email_address_id,
  )?.email_address;

  if (!primaryEmail) {
    console.error(`No primary email found for Clerk user ${clerkId}`);
    return NextResponse.json(
      { error: "No primary email address found" },
      { status: 400 },
    );
  }

try {
    const supabase = createAnonClient();
    const { error: insertError } = await supabase
      .from("users")
      .insert({ clerk_id: clerkId, email: primaryEmail });

    if (insertError) {
      // UNIQUE CONSTRAINT VIOLATION (Duplicate User)
      if (insertError.code === '23505') {
        console.log(`User ${clerkId} already exists in database. Ignoring retry.`);
        return NextResponse.json(
          { message: "User already synced" },
          { status: 200 } // Return 200 so Clerk stops retrying!
        );
      }

      console.error("Failed to insert user into Supabase:", insertError);
      return NextResponse.json(
        { error: "Failed to sync user to database" },
        { status: 500 },
      );
    }
  } catch (err) {
    console.error("Supabase insert error:", err);
    return NextResponse.json(
      { error: "Database operation failed" },
      { status: 500 },
    );
  }

  return NextResponse.json({ message: "User synced successfully" });
}