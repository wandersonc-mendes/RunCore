export function activityStartValue(activity) {
  return (
    activity?.start_date_local
    || activity?.start_date
    || activity?.start_at
    || null
  );
}


export function activityStartDate(activity) {
  const value = activityStartValue(activity);

  if (!value) return null;

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}


export function activityLocalDateKey(activity) {
  const date = activityStartDate(activity);

  if (!date) return "";

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}
