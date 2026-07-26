import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

const STORAGE_KEY = "runcore-theme";
const ThemeContext = createContext(null);

function systemTheme() {
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export function ThemeProvider({ children }) {
  const [preference, setPreference] = useState(
    () => localStorage.getItem(STORAGE_KEY) || "system",
  );
  const [resolvedTheme, setResolvedTheme] = useState(
    () => preference === "system" ? systemTheme() : preference,
  );

  useEffect(() => {
    const media = window.matchMedia(
      "(prefers-color-scheme: dark)",
    );

    function applyTheme() {
      const nextTheme = preference === "system"
        ? systemTheme()
        : preference;

      setResolvedTheme(nextTheme);
      document.documentElement.dataset.theme = nextTheme;
      document.documentElement.style.colorScheme = nextTheme;
    }

    applyTheme();

    if (preference === "system") {
      media.addEventListener("change", applyTheme);
    }

    return () => {
      media.removeEventListener("change", applyTheme);
    };
  }, [preference]);

  function changeTheme(nextPreference) {
    if (!["light", "dark", "system"].includes(nextPreference)) {
      return;
    }

    localStorage.setItem(STORAGE_KEY, nextPreference);
    setPreference(nextPreference);
  }

  const value = useMemo(
    () => ({
      preference,
      resolvedTheme,
      changeTheme,
    }),
    [preference, resolvedTheme],
  );

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);

  if (!context) {
    throw new Error(
      "useTheme deve ser usado dentro de ThemeProvider.",
    );
  }

  return context;
}
