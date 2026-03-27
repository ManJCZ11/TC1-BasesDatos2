import { useState } from "react";
import api from "../services/api";

export default function Register() {
  const [nombre, setNombre] = useState("");
  const [apellido, setApellido] = useState("");
  const [email, setEmail] = useState("");
  const [rol, setRol] = useState("Cliente");
  const [password, setPassword] = useState("");

  const handleRegister = async () => {
    try {
      await api.post("/auth/register", {
        nombre,
        apellido,
        email,
        rol,
        password
      });

      alert("Usuario creado correctamente ✅");

    } catch (err) {
      console.error(err.response?.data);
      alert("Error en registro");
    }
  };

  return (
    <div>
      <h2>Register</h2>

      <input
        placeholder="Nombre"
        onChange={(e) => setNombre(e.target.value)}
      />

      <input
        placeholder="Apellido"
        onChange={(e) => setApellido(e.target.value)}
      />

      <input
        placeholder="Email"
        onChange={(e) => setEmail(e.target.value)}
      />

      <input
        placeholder="Rol"
        value={rol}
        onChange={(e) => setRol(e.target.value)}
      />

      <input
        type="password"
        placeholder="Password"
        onChange={(e) => setPassword(e.target.value)}
      />

      <button onClick={handleRegister}>
        Registrar
      </button>
    </div>
  );
}