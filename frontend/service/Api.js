const BASE_URL = "http://127.0.0.1:8000";

export const getPosts = async () => {
  const response = await fetch(`${BASE_URL}/posts/no_auth`);

  if (!response.ok) {
    throw new Error("Failed to fetch posts");
  }

  return await response.json();
};

// 123