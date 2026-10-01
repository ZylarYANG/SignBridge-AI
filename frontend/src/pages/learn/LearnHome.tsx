import {
  useEffect,
  useState,
} from "react";

import {
  fetchSignCatalog,
  type CollectionSign,
} from "../../services/catalog";

import {
  PixelQuestWorld,
} from "../../components/learning/PixelQuestWorld";

export function LearnHome() {
  const [
    signs,
    setSigns,
  ] =
    useState<CollectionSign[]>([]);

  const [
    status,
    setStatus,
  ] =
    useState<
      "loading" |
      "ready" |
      "error"
    >(
      "loading"
    );

  useEffect(() => {
    let cancelled = false;

    async function loadCatalog() {
      try {
        const catalog =
          await fetchSignCatalog();

        if (cancelled) {
          return;
        }

        setSigns(
          catalog.signs
        );

        setStatus(
          "ready"
        );
      }
      catch (error) {
        console.error(
          "Pixel quest catalog failed:",
          error
        );

        if (!cancelled) {
          setStatus(
            "error"
          );
        }
      }
    }

    void loadCatalog();

    return () => {
      cancelled = true;
    };
  }, []);

  if (
    status ===
      "loading"
  ) {
    return (
      <main className="pq-state">
        <div className="pq-loading">
          <i />
          <i />
          <i />

          <span>
            SB
          </span>
        </div>
      </main>
    );
  }

  if (
    status ===
      "error"
  ) {
    return (
      <main className="pq-state pq-state-error">
        <div>
          <strong>
            !
          </strong>

          <span>
            BACKEND OFFLINE
          </span>
        </div>
      </main>
    );
  }

  return (
    <PixelQuestWorld
      signs={signs}
    />
  );
}
