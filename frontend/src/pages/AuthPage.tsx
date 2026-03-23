import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"

import { AuthPanel } from "../components/AuthPanel"
import { useAuth } from "../hooks/useAuth"

export function AuthPage() {
  const navigate = useNavigate()
  const { isAuthenticated, loading, error, login, register, clearError } = useAuth()
  const [mode, setMode] = useState<"login" | "register">("login")
  const [email, setEmail] = useState("demo@example.com")
  const [password, setPassword] = useState("demo12345")

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/app", { replace: true })
    }
  }, [isAuthenticated, navigate])

  const handleSubmit = async () => {
    if (mode === "login") {
      await login(email, password)
      return
    }
    await register(email, password)
  }

  return (
    <main className="auth-screen">
      <section className="auth-copy">
        <p className="eyebrow">Access Hub</p>
        <h1>Acceso claro primero. Operacion en tiempo real despues.</h1>
        <p className="hero-copy">
          La entrada al sistema vive en una vista dedicada. Cuando la sesion es valida, el usuario pasa al dashboard sin mezclar
          autenticacion con la gestion de reportes.
        </p>

        <div className="hero-band">
          <div className="hero-stat">
            <span>2</span>
            <p>colas de prioridad</p>
          </div>
          <div className="hero-stat">
            <span>Push</span>
            <p>estado en tiempo real</p>
          </div>
          <div className="hero-stat">
            <span>AWS</span>
            <p>metricas y salud del sistema</p>
          </div>
        </div>

        <div className="feature-stack">
          <article className="feature-card">
            <h3>Auth separada</h3>
            <p>Login y registro viven en un bloque dedicado, limpio y rapido de usar.</p>
          </article>
          <article className="feature-card">
            <h3>Panel operativo</h3>
            <p>El dashboard prioriza seguimiento de jobs, resultados y estado de conexion.</p>
          </article>
          <article className="feature-card">
            <h3>Prioridad visible</h3>
            <p>Los reportes criticos quedan identificados desde el alta hasta su procesamiento.</p>
          </article>
          <article className="feature-card">
            <h3>Responsive real</h3>
            <p>La interfaz funciona bien en desktop amplio y tambien en pantallas estrechas.</p>
          </article>
        </div>
      </section>

      <AuthPanel
        email={email}
        password={password}
        mode={mode}
        loading={loading}
        error={error}
        onEmailChange={(value) => {
          clearError()
          setEmail(value)
        }}
        onPasswordChange={(value) => {
          clearError()
          setPassword(value)
        }}
        onModeChange={(nextMode) => {
          clearError()
          setMode(nextMode)
        }}
        onSubmit={handleSubmit}
      />
    </main>
  )
}
