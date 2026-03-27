import { useState } from "react";
import api from "../services/api";
import { useNavigate } from "react-router-dom";

export default function Login() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const navigate = useNavigate();

    const handleLogin = async () => {
        try {
            const params = new URLSearchParams();
            params.append("username", email.trim());
            params.append("password", password);

            const res = await api.post("/auth/login", params, {
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            });

            localStorage.setItem("token", res.data.access_token);

            alert("Login exitoso ✅");

            // 🔥 REDIRECCIÓN
            navigate("/restaurants");

        } catch (err) {
            console.error(err.response?.data);
            alert("Error en login");
        }
    };

    return (
        <div>
            <h2>Login</h2>
            <input placeholder="email" onChange={(e) => setEmail(e.target.value)} />
            <input type="password" onChange={(e) => setPassword(e.target.value)} />
            <button onClick={handleLogin}>Login</button>
        </div>
    );
}