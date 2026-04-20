import { useEffect, useState } from "react";
import { getPosts } from "../services/Api";

function PostsPage() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await getPosts();
        console.log("Fetched posts:", data);
        setPosts(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);      // Empty dependency array means this runs once on mount/after first render

  if (loading) return <h2>Loading...</h2>;
  if (error) return <h2>Error: {error}</h2>;

  return (
    <div style={{ padding: "20px" }}>
      <h1>Posts</h1>

      {posts.length === 0 ? (
        <p>No posts found</p>
      ) : (
        posts.map((item) => (
          <div
            key={item.post.id}
            style={{
              border: "1px solid #ccc",
              padding: "10px",
              marginBottom: "10px",
              borderRadius: "8px",
              color: "black"
            }}
          >
            <h3>{item.post.title}</h3>
            <p>{item.post.content}</p>
          </div>
        ))
      )}
    </div>
  );
}

export default PostsPage;




// 🔁 Flow :
// Component renders
// UI shows (maybe empty state)
// useEffect runs after render
// API call happens
// Data comes back
// useState stores data
// React re-renders UI with new data

// 123