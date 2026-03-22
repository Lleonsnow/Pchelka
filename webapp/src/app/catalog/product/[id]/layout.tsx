import type { Metadata } from "next";

type Props = { children: React.ReactNode; params: { id: string } };

function serverApiBase(): string {
  const raw = (
    process.env.BACKEND_INTERNAL_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://127.0.0.1:8000"
  )
    .replace(/[\r\n\t]+/g, "")
    .trim();
  return raw.replace(/\/$/, "");
}

async function fetchProductForMeta(id: string) {
  const base = serverApiBase();
  const url = `${base}/api/webapp/catalog/products/${encodeURIComponent(id)}/`;
  try {
    const res = await fetch(url, { next: { revalidate: 120 } });
    if (!res.ok) return null;
    return (await res.json()) as {
      name?: string;
      description?: string;
      image_urls?: string[];
    };
  } catch {
    return null;
  }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const p = await fetchProductForMeta(params.id);
  if (!p?.name) {
    return { title: "Товар" };
  }
  const desc = (p.description || "")
    .replace(/[\r\n\t]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 160);
  const img = (p.image_urls || [])
    .map((u) => (typeof u === "string" ? u.replace(/[\r\n\t]+/g, "").trim() : ""))
    .find(Boolean);
  return {
    title: p.name,
    description: desc || undefined,
    openGraph: {
      title: p.name,
      description: desc || undefined,
      images: img ? [{ url: img }] : [],
    },
    twitter: {
      card: "summary_large_image",
      title: p.name,
      description: desc || undefined,
      images: img ? [img] : [],
    },
  };
}

export default function ProductLayout({ children }: { children: React.ReactNode }) {
  return children;
}
