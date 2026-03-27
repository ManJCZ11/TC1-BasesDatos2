import { useEffect, useState } from "react";
import api from "../services/api";

export default function Profile() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    api.get("/users/me")
      .then(res => {
        console.log("USER:", res.data);
        setUser(res.data);
      })
      .catch(err => {
        console.error("ERROR:", err.response?.data);
      });
  }, []);

  if (!user) return <p>Cargando perfil...</p>;

  return (
    <div>
      <h2>Mi Perfil</h2>

      <p><strong>Nombre:</strong> {user.nombre}</p>
      <p><strong>Email:</strong> {user.email}</p>
      <p><strong>Rol:</strong> {user.rol}</p>
    </div>
  );
}