import { useEffect, useState } from "react";

import { errorMessage } from "../api/client";

export function useAsyncData(loader, dependencies = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    loader()
      .then((result) => {
        if (active) {
          setData(result);
        }
      })
      .catch((requestError) => {
        if (active) {
          setError(errorMessage(requestError));
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, dependencies);

  return { data, loading, error, setData };
}
