// GlbUploader.tsx
// Sube archivos .glb a Supabase Storage y los lista, para alimentar a
// CustomJewelryViewer.tsx con modelUrl. Requiere que el proyecto de Lovable
// ya tenga la integración nativa de Supabase activada (Lovable la crea en
// src/integrations/supabase/client.ts) y que existan el bucket y la tabla
// definidos en supabase/schema.sql de este repo.
//
// Cómo usarlo en Lovable:
//   1. Crea src/components/GlbUploader.tsx y pega este contenido.
//   2. <GlbUploader onSelectModel={(url) => setModelUrl(url)} />

import { useEffect, useState } from "react";
import { supabase } from "@/integrations/supabase/client";

const BUCKET = "jewelry-models";
const TABLE = "jewelry_models";

type JewelryModel = {
  id: string;
  name: string;
  storage_path: string;
  created_at: string;
};

type Props = {
  onSelectModel: (url: string) => void;
};

export default function GlbUploader({ onSelectModel }: Props) {
  const [models, setModels] = useState<JewelryModel[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    const { data, error: fetchError } = await supabase
      .from(TABLE)
      .select("id, name, storage_path, created_at")
      .order("created_at", { ascending: false });
    if (fetchError) {
      setError(fetchError.message);
      return;
    }
    setModels(data ?? []);
  }

  useEffect(() => {
    refresh();
  }, []);

  function publicUrl(storagePath: string) {
    return supabase.storage.from(BUCKET).getPublicUrl(storagePath).data.publicUrl;
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".glb")) {
      setError("Solo se admiten archivos .glb");
      return;
    }

    setUploading(true);
    setError(null);
    try {
      const path = `${crypto.randomUUID()}-${file.name}`;
      const { error: uploadError } = await supabase.storage.from(BUCKET).upload(path, file);
      if (uploadError) throw uploadError;

      const { error: insertError } = await supabase
        .from(TABLE)
        .insert({ name: file.name, storage_path: path });
      if (insertError) throw insertError;

      await refresh();
      onSelectModel(publicUrl(path));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al subir el modelo");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <label>
        <span>Subir modelo .glb</span>
        <input type="file" accept=".glb" onChange={handleUpload} disabled={uploading} />
      </label>

      {uploading && <p>Subiendo…</p>}
      {error && <p style={{ color: "crimson" }}>{error}</p>}

      {models.length > 0 && (
        <div>
          <p>Modelos subidos</p>
          <ul style={{ listStyle: "none", padding: 0, display: "flex", flexDirection: "column", gap: 6 }}>
            {models.map((model) => (
              <li key={model.id}>
                <button type="button" onClick={() => onSelectModel(publicUrl(model.storage_path))}>
                  {model.name}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
