const ADMIN_GROUP =
  (process.env.VUE_APP_ADMIN_GROUP || "").trim() || "admin";

export function userIsAdmin(user) {
  if (
    !user ||
    !user.signInUserSession ||
    !user.signInUserSession.idToken ||
    !user.signInUserSession.idToken.payload
  ) {
    return false;
  }

  const groupsRaw =
    user.signInUserSession.idToken.payload["cognito:groups"];

  if (!groupsRaw) {
    return false;
  }

  if (Array.isArray(groupsRaw)) {
    return groupsRaw.includes(ADMIN_GROUP);
  }

  if (typeof groupsRaw === "string") {
    return groupsRaw
      .split(",")
      .map((group) => group.trim())
      .filter(Boolean)
      .includes(ADMIN_GROUP);
  }

  return false;
}

export function getAdminGroupName() {
  return ADMIN_GROUP;
}
