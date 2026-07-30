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
  return window.matchMedia(
    "(prefers-color-scheme: dark)",
  ).matches
    ? "dark"
    : "light";
}

function initialTheme() {
  const stored = localStorage.getItem(STORAGE_KEY);

  return stored === "dark" || stored === "light"
    ? stored
    : systemTheme();
}

export function ThemeProvider({ children }) {
  const [resolvedTheme, setResolvedTheme] = useState(
    initialTheme,
  );

  useEffect(() => {
    document.documentElement.dataset.theme = resolvedTheme;
    document.documentElement.style.colorScheme = resolvedTheme;
  }, [resolvedTheme]);

  function changeTheme(nextTheme) {
    if (!["light", "dark"].includes(nextTheme)) {
      return;
    }

    localStorage.setItem(STORAGE_KEY, nextTheme);
    setResolvedTheme(nextTheme);
  }

  function toggleTheme() {
    changeTheme(
      resolvedTheme === "dark"
        ? "light"
        : "dark",
    );
  }

  const value = useMemo(
    () => ({
      preference: resolvedTheme,
      resolvedTheme,
      changeTheme,
      toggleTheme,
    }),
    [resolvedTheme],
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
