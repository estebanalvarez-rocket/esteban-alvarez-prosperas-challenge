interface AuthPanelProps {
  email: string
  password: string
  mode: "login" | "register"
  loading: boolean
  error: string | null
  onEmailChange: (value: string) => void
  onPasswordChange: (value: string) => void
  onModeChange: (mode: "login" | "register") => void
  onSubmit: () => void
}

export function AuthPanel(props: AuthPanelProps) {
  const { email, password, mode, loading, error, onEmailChange, onPasswordChange, onModeChange, onSubmit } = props

  return (
    <section className="panel auth-panel">
      <div className="panel-header">
        <p className="eyebrow">Acceso</p>
        <h2>{mode === "login" ? "Inicia sesion" : "Crea un usuario de prueba"}</h2>
        <p className="section-copy">
          Usa el acceso de demo o crea una cuenta rapida para entrar al panel de operaciones.
        </p>
      </div>

      <div className="segmented">
        <button className={mode === "login" ? "active" : ""} onClick={() => onModeChange("login")} type="button">
          Login
        </button>
        <button className={mode === "register" ? "active" : ""} onClick={() => onModeChange("register")} type="button">
          Registro
        </button>
      </div>

      <label>
        Email
        <input type="email" value={email} onChange={(event) => onEmailChange(event.target.value)} />
      </label>

      <label>
        Password
        <input type="password" value={password} onChange={(event) => onPasswordChange(event.target.value)} />
      </label>

      {error ? <div className="feedback error">{error}</div> : null}

      <button className="primary-button" disabled={loading} onClick={onSubmit} type="button">
        {loading ? "Procesando..." : mode === "login" ? "Entrar" : "Registrar"}
      </button>

      <div className="auth-footnote">
        <span>Demo sugerida:</span>
        <strong>demo@example.com</strong>
      </div>
    </section>
  )
}
