import { useEffect, useState } from "react";
import api from "../services/api";

export default function Restaurants() {
  const [data, setData] = useState([]);

  useEffect(() => {
    api.get("/restaurants")
      .then(res => setData(res.data));
  }, []);

  return (
    <div>
      <h2>Restaurantes</h2>

      {data.map((r) => (
        <div key={r.id}>
          <h3>{r.name}</h3>
          <p>{r.description}</p>
        </div>
      ))}
    </div>
  );
}