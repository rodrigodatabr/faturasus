import { useState, useRef, useEffect } from "react";
import { Camera, Mic, Check, X, Send, Loader, Circle, ScanLine, ArrowUp, ClipboardCheck, Clock, AlertCircle } from "lucide-react";

const BLUE = "#1B4F72";
const BLUE_LIGHT = "#D6EAF8";
const GREEN = "#1E8449";
const GREEN_LIGHT = "#D5F5E3";
const GRAY_BG = "#F8F9FA";
const GRAY_TEXT = "#6C757D";
const RED = "#C0392B";

const DEMO_PATIENT = {
  cns: "704 2012 0546 8582",
  nome: "Maria Aparecida da Silva",
  sexo: "Feminino",
  idade: "44 anos",
  municipio: "Iguatama - MG",
};

const DEMO_PROCEDURE = {
  descricao: "Videocolonoscopia",
  codigo: "02.09.01.003-7",
  cid: "K63.5",
  valor: "R$ 145,43",
};

function BotMessage({ children, typing, delay = 0 }) {
  const [visible, setVisible] = useState(delay === 0);
  const [showContent, setShowContent] = useState(!typing);

  useEffect(() => {
    if (delay > 0) {
      const t = setTimeout(() => setVisible(true), delay);
      return () => clearTimeout(t);
    }
  }, [delay]);

  useEffect(() => {
    if (visible && typing) {
      const t = setTimeout(() => setShowContent(true), 800);
      return () => clearTimeout(t);
    }
  }, [visible, typing]);

  if (!visible) return null;

  return (
    <div style={{ display: "flex", gap: 8, marginBottom: 12, alignItems: "flex-end", animation: "fadeIn 0.3s ease" }}>
      <div style={{ width: 28, height: 28, borderRadius: "50%", background: BLUE, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
        <span style={{ color: "#fff", fontSize: 12, fontWeight: 700 }}>F</span>
      </div>
      <div style={{ background: "#fff", borderRadius: "2px 14px 14px 14px", padding: "10px 14px", maxWidth: "82%", boxShadow: "0 1px 3px rgba(0,0,0,0.06)", border: "1px solid #E8E8E8" }}>
        {showContent ? children : (
          <div style={{ display: "flex", gap: 5, padding: "4px 8px", alignItems: "center" }}>
            <span className="typing-dot" style={{ animationDelay: "0s" }} />
            <span className="typing-dot" style={{ animationDelay: "0.15s" }} />
            <span className="typing-dot" style={{ animationDelay: "0.3s" }} />
          </div>
        )}
      </div>
    </div>
  );
}

function UserMessage({ children }) {
  return (
    <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 12, animation: "fadeIn 0.3s ease" }}>
      <div style={{ background: BLUE, borderRadius: "14px 2px 14px 14px", padding: "10px 14px", maxWidth: "80%", color: "#fff", fontSize: 14 }}>
        {children}
      </div>
    </div>
  );
}

function CheckItem({ label, value, ok = true }) {
  return (
    <div style={{ display: "flex", gap: 6, alignItems: "flex-start", marginBottom: 4, fontSize: 13 }}>
      <span style={{ flexShrink: 0, marginTop: 2 }}>
        {ok
          ? <Check size={13} color={GREEN} strokeWidth={3} />
          : <X size={13} color="#E74C3C" strokeWidth={3} />
        }
      </span>
      <span><span style={{ color: GRAY_TEXT }}>{label}:</span> <strong>{value}</strong></span>
    </div>
  );
}

function QuickReply({ text, selected, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: "7px 16px", borderRadius: 20,
        border: selected ? `2px solid ${BLUE}` : "1.5px solid #D0D0D0",
        background: selected ? BLUE_LIGHT : "#fff",
        color: selected ? BLUE : "#333",
        fontWeight: selected ? 600 : 400,
        fontSize: 13, cursor: "pointer",
        transition: "all 0.2s",
      }}
    >
      {text}
    </button>
  );
}

function WaveformBars() {
  const heights = useRef([...Array(12)].map(() => 6 + Math.random() * 14));
  const speeds = useRef([...Array(12)].map(() => 0.5 + Math.random() * 0.5));
  return (
    <div style={{ display: "flex", gap: 2, alignItems: "center" }}>
      {heights.current.map((h, i) => (
        <div key={i} style={{
          width: 3, borderRadius: 2, height: h,
          background: "rgba(255,255,255,0.7)",
          animation: `pulse ${speeds.current[i]}s ease infinite`,
        }} />
      ))}
    </div>
  );
}

function CameraScanner({ onSuccess, onClose }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [flash, setFlash] = useState(false);
  const [camError, setCamError] = useState(false);

  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
      .then((s) => {
        streamRef.current = s;
        if (videoRef.current) videoRef.current.srcObject = s;
        const t = setTimeout(() => {
          setFlash(true);
          setTimeout(() => {
            s.getTracks().forEach((t) => t.stop());
            onSuccess();
          }, 350);
        }, 2200);
        return () => clearTimeout(t);
      })
      .catch(() => setCamError(true));
    return () => streamRef.current?.getTracks().forEach((t) => t.stop());
  }, []);

  function handleClose() {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    onClose();
  }

  if (camError) {
    return (
      <div style={{ position: "absolute", inset: 0, zIndex: 20, background: "rgba(0,0,0,0.85)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 12, padding: 24 }}>
        <ScanLine size={40} color="#fff" />
        <p style={{ color: "#fff", textAlign: "center", fontSize: 14 }}>Câmera não disponível neste dispositivo.</p>
        <button onClick={handleClose} style={{ padding: "10px 24px", borderRadius: 20, border: "none", background: "#fff", fontWeight: 600, cursor: "pointer" }}>Voltar</button>
      </div>
    );
  }

  return (
    <div style={{ position: "absolute", inset: 0, zIndex: 20, background: "#000", display: "flex", flexDirection: "column" }}>
      {flash && <div style={{ position: "absolute", inset: 0, background: "#fff", zIndex: 30, animation: "flashOut 0.35s ease forwards" }} />}
      <video ref={videoRef} autoPlay playsInline muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />

      {/* overlay escuro com janela de scan */}
      <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
        <div style={{ width: "100%", height: "30%", background: "rgba(0,0,0,0.55)" }} />
        <div style={{ display: "flex", width: "100%", height: 90 }}>
          <div style={{ flex: 1, background: "rgba(0,0,0,0.55)" }} />
          <div style={{ width: 280, position: "relative", overflow: "hidden", borderRadius: 6, outline: "2px solid rgba(255,255,255,0.8)" }}>
            <div style={{ position: "absolute", left: 0, right: 0, height: 2, background: "#00E676", boxShadow: "0 0 8px #00E676", animation: "scanLine 1.4s ease-in-out infinite alternate" }} />
          </div>
          <div style={{ flex: 1, background: "rgba(0,0,0,0.55)" }} />
        </div>
        <div style={{ width: "100%", flex: 1, background: "rgba(0,0,0,0.55)", display: "flex", flexDirection: "column", alignItems: "center", paddingTop: 16, gap: 8 }}>
          <span style={{ color: "#fff", fontSize: 13 }}>Aponte para o código de barras do cartão</span>
        </div>
      </div>

      <button onClick={handleClose} style={{ position: "absolute", top: 14, right: 14, background: "rgba(0,0,0,0.5)", border: "1px solid rgba(255,255,255,0.3)", color: "#fff", padding: "7px 16px", borderRadius: 20, cursor: "pointer", fontSize: 13 }}>
        Cancelar
      </button>
    </div>
  );
}

function InputModal({ mode, onSuccess, onClose }) {
  const [value, setValue] = useState("");
  const isCpf = mode === "cpf";
  const maxRaw = isCpf ? 11 : 15;

  function formatValue(raw) {
    const d = raw.replace(/\D/g, "").slice(0, maxRaw);
    if (isCpf) {
      return d.replace(/(\d{3})(\d{3})(\d{3})(\d{0,2})/, (_, a, b, c, e) =>
        [a, b, c].filter(Boolean).join(".") + (e ? `-${e}` : "")
      );
    }
    return d.replace(/(\d{3})(\d{4})(\d{4})(\d{0,4})/, (_, a, b, c, e) =>
      [a, b, c, e].filter(Boolean).join(" ")
    );
  }

  const raw = value.replace(/\D/g, "");
  const ready = raw.length === maxRaw;

  return (
    <div style={{ position: "absolute", inset: 0, zIndex: 20, background: "rgba(0,0,0,0.6)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 24 }}>
      <div style={{ background: "#fff", borderRadius: 16, padding: 24, width: "100%", maxWidth: 320 }}>
        <div style={{ fontSize: 15, fontWeight: 700, color: BLUE, marginBottom: 16 }}>
          {isCpf ? "Digite o CPF do paciente" : "Digite o CNS do paciente"}
        </div>
        <input
          autoFocus
          type="tel"
          inputMode="numeric"
          placeholder={isCpf ? "000.000.000-00" : "000 0000 0000 0000"}
          value={value}
          onChange={(e) => setValue(formatValue(e.target.value))}
          style={{ width: "100%", height: 44, borderRadius: 10, border: `1.5px solid ${ready ? GREEN : "#DDD"}`, padding: "0 14px", fontSize: 18, fontFamily: "monospace", outline: "none", boxSizing: "border-box", letterSpacing: 1 }}
        />
        <div style={{ fontSize: 11, color: GRAY_TEXT, marginTop: 6 }}>
          {isCpf ? "11 dígitos" : "15 dígitos"} — {raw.length}/{maxRaw}
        </div>
        <button
          onClick={() => ready && onSuccess()}
          style={{ marginTop: 16, width: "100%", padding: "12px 0", borderRadius: 10, border: "none", background: ready ? GREEN : "#E0E0E0", color: ready ? "#fff" : "#999", fontWeight: 700, fontSize: 14, cursor: ready ? "pointer" : "default", transition: "all 0.2s" }}
        >
          Confirmar
        </button>
        <button onClick={onClose} style={{ marginTop: 8, width: "100%", padding: "10px 0", borderRadius: 10, border: `1px solid #DDD`, background: "#fff", color: GRAY_TEXT, fontSize: 13, cursor: "pointer" }}>
          Cancelar
        </button>
      </div>
    </div>
  );
}

function StatCard({ icon, value, label, bgColor, color }) {
  return (
    <div style={{ flex: 1, background: bgColor, borderRadius: 8, padding: "8px 10px", textAlign: "center" }}>
      <div style={{ display: "flex", justifyContent: "center", marginBottom: 2 }}>{icon}</div>
      <div style={{ fontSize: 20, fontWeight: 700, color }}>{value}</div>
      <div style={{ fontSize: 10, color }}>{label}</div>
    </div>
  );
}

export default function App() {
  const [step, setStep] = useState(0);
  const [scanning, setScanning] = useState(false);
  const [recording, setRecording] = useState(false);
  const [biopsia, setBiopsia] = useState(null);
  const [confirmed, setConfirmed] = useState(false);
  const [showStats, setShowStats] = useState(false);
  const [isMobile, setIsMobile] = useState(() => window.innerWidth <= 480);
  const [showCamera, setShowCamera] = useState(false);
  const [inputMode, setInputMode] = useState(null); // 'cpf' | 'cns'
  const [transcricaoTexto, setTranscricaoTexto] = useState('');
  const [transcricaoErro, setTranscricaoErro] = useState(null);
  const chatRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  useEffect(() => {
    const mq = window.matchMedia("(max-width: 480px)");
    const handler = (e) => setIsMobile(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [step, biopsia, confirmed, showStats]);

  function handleScan() {
    if (step > 0 || scanning) return;
    setShowCamera(true);
  }

  function handleScanSuccess() {
    setShowCamera(false);
    setScanning(true);
    setTimeout(() => { setScanning(false); setStep(1); }, 1500);
  }

  function handleInputSuccess() {
    setInputMode(null);
    setScanning(true);
    setTimeout(() => { setScanning(false); setStep(1); }, 1200);
  }

  async function handleMic() {
    if (step !== 1) return;
    if (recording) {
      mediaRecorderRef.current?.stop();
      return;
    }
    setTranscricaoErro(null);
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setTranscricaoErro('Permissão para microfone negada.');
      return;
    }
    const recorder = new MediaRecorder(stream);
    chunksRef.current = [];
    recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
    recorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      const blob = new Blob(chunksRef.current, { type: recorder.mimeType });
      const form = new FormData();
      form.append('audio', blob, 'audio.webm');
      try {
        const res = await fetch('/transcricao', { method: 'POST', body: form });
        if (!res.ok) throw new Error(await res.text());
        const { texto } = await res.json();
        setTranscricaoTexto(texto);
        setStep(2);
      } catch {
        setTranscricaoErro('Falha na transcrição. Tente novamente.');
      } finally {
        setRecording(false);
      }
    };
    mediaRecorderRef.current = recorder;
    recorder.start();
    setRecording(true);
  }

  function handleBiopsia(val) {
    setBiopsia(val);
    setTimeout(() => setStep(3), 500);
  }

  function handleConfirm() {
    setConfirmed(true);
    setTimeout(() => setShowStats(true), 600);
  }

  function handleReset() {
    setStep(0); setScanning(false); setRecording(false);
    setBiopsia(null); setConfirmed(false); setShowStats(false);
    setTranscricaoTexto(''); setTranscricaoErro(null);
  }

  const procedureComplete = step >= 3 && biopsia !== null;

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: 0, fontFamily: "'DM Sans', 'Helvetica Neue', sans-serif" }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet" />
      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.08); } }
        @keyframes rec { 0%, 100% { box-shadow: 0 0 0 0 rgba(192,57,43,0.4); } 50% { box-shadow: 0 0 0 12px rgba(192,57,43,0); } }
        @keyframes scanLine { from { top: 5%; } to { top: 95%; } }
        @keyframes flashOut { from { opacity: 0.85; } to { opacity: 0; } }
        .typing-dot { width: 6px; height: 6px; background: #999; border-radius: 50%; animation: pulse 1s ease-in-out infinite; display: inline-block; }
        .action-btn { transition: all 0.15s ease; }
        .action-btn:active { transform: scale(0.95); }
      `}</style>

      {/* PHONE FRAME */}
      <div style={{
        width: isMobile ? "100%" : 375,
        height: isMobile ? "100dvh" : 780,
        background: GRAY_BG,
        borderRadius: isMobile ? 0 : 32,
        overflow: "hidden", display: "flex", flexDirection: "column",
        boxShadow: isMobile ? "none" : "0 8px 40px rgba(0,0,0,0.12), 0 2px 8px rgba(0,0,0,0.06)",
        border: isMobile ? "none" : "6px solid #1a1a1a",
        position: "relative",
      }}>
        {showCamera && <CameraScanner onSuccess={handleScanSuccess} onClose={() => setShowCamera(false)} />}
        {inputMode && <InputModal mode={inputMode} onSuccess={handleInputSuccess} onClose={() => setInputMode(null)} />}

        {/* HEADER */}
        <div style={{ height: 44, background: BLUE, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <span style={{ color: "#fff", fontSize: 15, fontWeight: 700, letterSpacing: 1.5 }}>FaturaSUS</span>
        </div>

        {/* PROFESSIONAL BADGE */}
        <div style={{ background: "#fff", padding: "8px 16px", display: "flex", alignItems: "center", gap: 10, borderBottom: "1px solid #ECECEC", flexShrink: 0 }}>
          <div style={{ width: 34, height: 34, borderRadius: "50%", background: BLUE_LIGHT, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <span style={{ fontSize: 14, fontWeight: 700, color: BLUE }}>CM</span>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: "#222" }}>Dra. Daniela Cerveira Poletto</div>
            <div style={{ fontSize: 11, color: GRAY_TEXT }}>{"Gastroenterologista \u2022 Policl\u00EDnica Iguatama"}</div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: GREEN }}>Mar/2026</div>
            <div style={{ fontSize: 10, color: GRAY_TEXT }}>487 registros</div>
          </div>
        </div>

        {/* CHAT */}
        <div ref={chatRef} style={{ flex: 1, overflowY: "auto", padding: "12px 12px 8px", display: "flex", flexDirection: "column" }}>

          {step === 0 && !scanning && (
            <BotMessage>
              <div style={{ fontSize: 13, lineHeight: 1.5 }}>
                {"Ol\u00E1, Dra. Daniela! Escaneie o cart\u00E3o SUS do paciente para come\u00E7ar o registro."}
              </div>
            </BotMessage>
          )}

          {scanning && (
            <BotMessage typing>
              <div style={{ fontSize: 13, display: "flex", alignItems: "center", gap: 6 }}>
                <ScanLine size={14} color={BLUE} />
                {"Lendo c\u00F3digo de barras..."}
              </div>
            </BotMessage>
          )}

          {step >= 1 && (
            <BotMessage>
              <div style={{ fontSize: 13, marginBottom: 8, fontWeight: 600, color: GREEN, display: "flex", alignItems: "center", gap: 5 }}>
                <Check size={14} strokeWidth={3} /> {"Paciente identificada via CADSUS"}
              </div>
              <CheckItem label="Nome" value={DEMO_PATIENT.nome} />
              <CheckItem label="CNS" value={DEMO_PATIENT.cns} />
              <CheckItem label="Sexo" value={`${DEMO_PATIENT.sexo}, ${DEMO_PATIENT.idade}`} />
              <CheckItem label={"Munic\u00EDpio"} value={DEMO_PATIENT.municipio} />
              <div style={{ marginTop: 8, fontSize: 12, color: GRAY_TEXT, fontStyle: "italic" }}>
                {"Agora grave um \u00E1udio descrevendo o procedimento."}
              </div>
            </BotMessage>
          )}

          {recording && (
            <UserMessage>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Mic size={16} />
                <WaveformBars />
                <span style={{ fontSize: 12 }}>Gravando... (toque novamente para parar)</span>
              </div>
            </UserMessage>
          )}

          {transcricaoErro && (
            <BotMessage>
              <span style={{ color: "#c0392b", fontSize: 13 }}>{transcricaoErro}</span>
            </BotMessage>
          )}

          {step >= 2 && (
            <>
              <UserMessage>
                <div style={{ fontSize: 13, display: "flex", alignItems: "center", gap: 6 }}>
                  <Mic size={14} />
                  <em>"{transcricaoTexto}"</em>
                </div>
              </UserMessage>
              <BotMessage>
                <div style={{ fontSize: 13, marginBottom: 8, fontWeight: 600, color: BLUE }}>
                  Procedimento identificado na SIGTAP
                </div>
                <CheckItem label="Procedimento" value={DEMO_PROCEDURE.descricao} />
                <CheckItem label={"C\u00F3digo"} value={DEMO_PROCEDURE.codigo} />
                <CheckItem label="CID" value={`${DEMO_PROCEDURE.cid} \u2014 P\u00F3lipo do c\u00F3lon`} />
                <CheckItem label="Valor SIGTAP" value={DEMO_PROCEDURE.valor} />
              </BotMessage>
              <BotMessage>
                <div style={{ fontSize: 13, marginBottom: 8 }}>
                  {"A colonoscopia foi realizada "}
                  <strong>{"com bi\u00F3psia"}</strong>?
                </div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <QuickReply text={"Sim, com bi\u00F3psia"} selected={biopsia === true} onClick={() => handleBiopsia(true)} />
                  <QuickReply text={"N\u00E3o, sem bi\u00F3psia"} selected={biopsia === false} onClick={() => handleBiopsia(false)} />
                </div>
              </BotMessage>
            </>
          )}

          {step >= 3 && biopsia !== null && (
            <>
              <UserMessage>
                <span style={{ fontSize: 13 }}>{biopsia ? "Sim, com bi\u00F3psia" : "N\u00E3o, sem bi\u00F3psia"}</span>
              </UserMessage>
              {biopsia && (
                <BotMessage>
                  <div style={{ fontSize: 13 }}>
                    <CheckItem label="Procedimento adicional" value={"Bi\u00F3psia de intestino grosso por endoscopia"} />
                    <CheckItem label={"C\u00F3digo"} value="02.01.01.031-0" />
                    <CheckItem label="Valor adicional" value="R$ 26,84" />
                  </div>
                </BotMessage>
              )}
              <BotMessage>
                <div style={{ fontSize: 13, marginBottom: 6, fontWeight: 600, color: GREEN, display: "flex", alignItems: "center", gap: 5 }}>
                  <Check size={14} strokeWidth={3} /> {"Todas as valida\u00E7\u00F5es aprovadas"}
                </div>
                <div style={{ fontSize: 12, marginBottom: 10 }}>
                  <CheckItem label={"CBO compat\u00EDvel"} value={"Sim \u2014 Gastroenterologista"} />
                  <CheckItem label="CNES habilitado" value="Sim" />
                </div>

                <div style={{ background: GRAY_BG, borderRadius: 10, padding: 12, marginBottom: 10, border: "1px solid #E0E0E0" }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: BLUE, marginBottom: 8, textTransform: "uppercase", letterSpacing: 0.5 }}>
                    Resumo do registro
                  </div>
                  <div style={{ fontSize: 12, lineHeight: 1.8 }}>
                    <div><strong>Paciente:</strong> {DEMO_PATIENT.nome}</div>
                    <div><strong>CNS:</strong> {DEMO_PATIENT.cns}</div>
                    <div><strong>Procedimento:</strong> {DEMO_PROCEDURE.descricao} ({DEMO_PROCEDURE.codigo})</div>
                    {biopsia && <div><strong>Adicional:</strong> {"Bi\u00F3psia intestino grosso (02.01.01.031-0)"}</div>}
                    <div><strong>CID:</strong> {DEMO_PROCEDURE.cid} {"\u2014 P\u00F3lipo do c\u00F3lon"}</div>
                    <div><strong>Data:</strong> 19/03/2026</div>
                    <div><strong>Valor total:</strong> {biopsia ? "R$ 172,27" : DEMO_PROCEDURE.valor}</div>
                  </div>
                </div>

                {!confirmed ? (
                  <button
                    onClick={handleConfirm}
                    style={{
                      width: "100%", padding: "12px 0", borderRadius: 12,
                      border: "none", background: GREEN, color: "#fff",
                      fontSize: 14, fontWeight: 700, cursor: "pointer",
                      display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
                      transition: "all 0.2s",
                    }}
                  >
                    <Check size={16} strokeWidth={3} /> Confirmar registro
                  </button>
                ) : (
                  <div style={{
                    textAlign: "center", padding: "10px 0", color: GREEN, fontWeight: 700, fontSize: 14,
                    display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
                    animation: "fadeIn 0.4s ease",
                  }}>
                    <Check size={18} strokeWidth={3} /> Registro salvo com sucesso!
                  </div>
                )}
              </BotMessage>
            </>
          )}

          {showStats && (
            <BotMessage>
              <div style={{ fontSize: 12, color: GRAY_TEXT, marginBottom: 6 }}>
                Seu dia at\u00E9 agora:
              </div>
              <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
                <StatCard
                  icon={<ClipboardCheck size={16} color={GREEN} />}
                  value="12"
                  label="Registros hoje"
                  bgColor={GREEN_LIGHT}
                  color={GREEN}
                />
                <StatCard
                  icon={<AlertCircle size={16} color="#B7950B" />}
                  value="1"
                  label="Pendente"
                  bgColor="#FEF9E7"
                  color="#B7950B"
                />
                <StatCard
                  icon={<Clock size={16} color={BLUE} />}
                  value="18s"
                  label={"Tempo m\u00E9dio"}
                  bgColor={BLUE_LIGHT}
                  color={BLUE}
                />
              </div>
              <div style={{ fontSize: 12, color: GRAY_TEXT, marginBottom: 4 }}>
                {"\u00DAltimo: Maria Aparecida da Silva \u2014 Videocolonoscopia"}
              </div>
              <div style={{ fontSize: 11, color: "#B7950B", display: "flex", alignItems: "center", gap: 4, marginBottom: 8 }}>
                <AlertCircle size={12} />
                {"1 registro incompleto (falta CID). Toque para completar."}
              </div>
              <button
                onClick={handleReset}
                style={{
                  marginTop: 4, width: "100%", padding: "10px 0", borderRadius: 10,
                  border: `1.5px solid ${BLUE}`, background: "#fff", color: BLUE,
                  fontSize: 13, fontWeight: 600, cursor: "pointer",
                }}
              >
                Novo registro
              </button>
            </BotMessage>
          )}
        </div>

        {/* TEXT INPUT + MIC */}
        <div style={{ padding: "6px 12px", background: "#fff", borderTop: "1px solid #ECECEC", display: "flex", gap: 8, alignItems: "center", flexShrink: 0 }}>
          <input
            type="text"
            placeholder="Digite uma mensagem..."
            style={{
              flex: 1, height: 38, borderRadius: 20, border: "1.5px solid #DDD",
              padding: "0 16px", fontSize: 13, outline: "none", background: GRAY_BG, color: "#333",
              fontFamily: "inherit",
            }}
          />
          <button style={{
            width: 38, height: 38, borderRadius: "50%", border: "1.5px solid #DDD",
            background: "#fff", cursor: "pointer",
            display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
          }}>
            <Mic size={18} color={GRAY_TEXT} />
          </button>
          <button style={{
            width: 38, height: 38, borderRadius: "50%", border: "none",
            background: BLUE, cursor: "pointer",
            display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
          }}>
            <ArrowUp size={18} color="#fff" strokeWidth={2.5} />
          </button>
        </div>

        {/* MAIN ACTION BUTTONS */}
        <div style={{ display: "flex", gap: 10, padding: "6px 12px 0", background: "#fff", flexShrink: 0 }}>
          <button
            className="action-btn"
            onClick={handleScan}
            style={{
              flex: 1, height: 80, borderRadius: 18, border: "none",
              cursor: step > 0 ? "default" : "pointer",
              background: step > 0 ? GREEN_LIGHT : scanning ? "#FFF3CD" : BLUE_LIGHT,
              display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6,
              opacity: step > 0 && !scanning ? 0.55 : 1,
            }}
          >
            {step > 0
              ? <Check size={28} color={GREEN} strokeWidth={2.5} />
              : scanning
                ? <Loader size={28} color="#B7950B" strokeWidth={2} style={{ animation: "pulse 1s ease infinite" }} />
                : <Camera size={28} color={BLUE} strokeWidth={1.8} />
            }
            <span style={{ fontSize: 13, fontWeight: 600, color: step > 0 ? GREEN : scanning ? "#B7950B" : BLUE }}>
              {step > 0 ? "Paciente OK" : scanning ? "Escaneando..." : "Escanear cart\u00E3o"}
            </span>
          </button>

          <button
            className="action-btn"
            onClick={handleMic}
            style={{
              flex: 1, height: 80, borderRadius: 18, border: "none",
              cursor: step === 1 ? "pointer" : "default",
              background: recording ? "#FADBD8" : procedureComplete ? GREEN_LIGHT : step === 1 ? BLUE_LIGHT : "#F0F0F0",
              display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6,
              animation: recording ? "rec 1.5s ease infinite" : "none",
              opacity: step < 1 ? 0.35 : (step > 1 && !procedureComplete) ? 0.65 : 1,
            }}
          >
            {procedureComplete
              ? <Check size={28} color={GREEN} strokeWidth={2.5} />
              : recording
                ? <Circle size={28} color={RED} fill={RED} strokeWidth={0} />
                : <Mic size={28} color={step === 1 ? BLUE : "#999"} strokeWidth={1.8} />
            }
            <span style={{ fontSize: 13, fontWeight: 600, color: procedureComplete ? GREEN : recording ? RED : step === 1 ? BLUE : "#999" }}>
              {procedureComplete ? "Procedimento OK" : recording ? "Gravando..." : "Gravar procedimento"}
            </span>
          </button>
        </div>
        {/* FALLBACK ID OPTIONS */}
        {step === 0 && !scanning && (
          <div style={{ background: "#fff", padding: "6px 12px 14px", display: "flex", justifyContent: "center", gap: 24, flexShrink: 0 }}>
            <button onClick={() => setInputMode("cpf")} style={{ background: "none", border: "none", color: GRAY_TEXT, fontSize: 12, cursor: "pointer", textDecoration: "underline" }}>
              Digitar CPF
            </button>
            <button onClick={() => setInputMode("cns")} style={{ background: "none", border: "none", color: GRAY_TEXT, fontSize: 12, cursor: "pointer", textDecoration: "underline" }}>
              Digitar CNS
            </button>
          </div>
        )}
        {step > 0 && <div style={{ background: "#fff", height: 14, flexShrink: 0 }} />}
      </div>

      {!isMobile && (
        <div style={{ marginTop: 16, textAlign: "center", maxWidth: 375 }}>
          <div style={{ fontSize: 12, color: GRAY_TEXT, lineHeight: 1.6 }}>
            {"Prot\u00F3tipo interativo \u2022 Toque nos bot\u00F5es para simular o fluxo"}
          </div>
        </div>
      )}
    </div>
  );
}