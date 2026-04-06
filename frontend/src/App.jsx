import { useState, useRef, useEffect } from "react";
import { Camera, Mic, Check, X, Loader, Circle, ScanLine, ArrowUp, ClipboardCheck, Clock, AlertCircle, RotateCcw, Plus, Hourglass } from "lucide-react";

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

const DEMO_PROFISSIONAL = {
  id: "00000000-0000-0000-0000-000000000001",
  cbo: "322205",         // Técnico em Enfermagem
  cnes: "2139200",       // PSF Vila Nova — Três Pontas/MG
  nome: "Vanessa Aparecida Gonçalves",
  especialidade: "Técnica de Enfermagem",
  estabelecimento: "PSF Vila Nova — Três Pontas/MG",
  iniciais: "VG",
};

// Competência derivada dinamicamente da data atual (AAAAMM)
function competenciaAtual() {
  const hoje = new Date();
  return `${hoje.getFullYear()}${String(hoje.getMonth() + 1).padStart(2, "0")}`;
}

function competenciaLabel() {
  const hoje = new Date();
  const meses = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"];
  return `${meses[hoje.getMonth()]}/${hoje.getFullYear()}`;
}


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
          {/* Banner de simulação */}
          <div style={{ background: "#FFC107", color: "#333", fontSize: 12, fontWeight: 600, borderRadius: 8, padding: "8px 14px", maxWidth: 280, textAlign: "center", lineHeight: 1.4, marginTop: 8 }}>
            SIMULAÇÃO. A leitura real do Cartão SUS estará disponível após integração com esta unidade.
          </div>
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
  // step 0 = identificar paciente, step 1 = gravar procedimento, step 2+ = classificação/validação
  // Abre direto no step 1 (paciente DEMO já identificado para o demo)
  const [step, setStep] = useState(1);
  const [scanning, setScanning] = useState(false);
  const [recording, setRecording] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [btnReady, setBtnReady] = useState(false); // botão inferior voltou ao microfone após confirmação
  const [confirmed, setConfirmed] = useState(false);
  const [showStats, setShowStats] = useState(false);
  const [isMobile, setIsMobile] = useState(() => window.innerWidth <= 480);
  const [showCamera, setShowCamera] = useState(false);
  const [inputMode, setInputMode] = useState(null); // 'cpf' | 'cns'
  const [transcricaoTexto, setTranscricaoTexto] = useState('');
  const [transcricaoErro, setTranscricaoErro] = useState(null);
  const [procedure, setProcedure] = useState(null);
  const [procedureErro, setProcedureErro] = useState(null);
  // Lista de procedimentos confirmados para o mesmo paciente
  const [procedures, setProcedures] = useState([]);
  const [validacaoResultado, setValidacaoResultado] = useState(null);
  const [validacaoLoading, setValidacaoLoading] = useState(false);
  const chatRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const silenceTimerRef = useRef(null);
  const analyserRef = useRef(null);

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
  }, [step, confirmed, showStats, procedures]);

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

  function stopRecording() {
    clearInterval(silenceTimerRef.current);
    mediaRecorderRef.current?.stop();
  }

  async function handleMic() {
    if (step !== 1) return;
    if (recording) {
      stopRecording();
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

    // Detecção de silêncio via AnalyserNode
    const audioCtx = new AudioContext();
    const source = audioCtx.createMediaStreamSource(stream);
    const analyser = audioCtx.createAnalyser();
    analyser.fftSize = 512;
    source.connect(analyser);
    analyserRef.current = analyser;
    const dataArray = new Uint8Array(analyser.fftSize);
    let silenceStart = null;
    const SILENCE_THRESHOLD = 10; // amplitude média abaixo disso = silêncio
    const SILENCE_DURATION = 1800; // ms de silêncio para parar
    silenceTimerRef.current = setInterval(() => {
      analyser.getByteTimeDomainData(dataArray);
      const avg = dataArray.reduce((s, v) => s + Math.abs(v - 128), 0) / dataArray.length;
      if (avg < SILENCE_THRESHOLD) {
        if (!silenceStart) silenceStart = Date.now();
        else if (Date.now() - silenceStart > SILENCE_DURATION) stopRecording();
      } else {
        silenceStart = null;
      }
    }, 100);

    const recorder = new MediaRecorder(stream);
    chunksRef.current = [];
    recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
    recorder.onstop = async () => {
      clearInterval(silenceTimerRef.current);
      stream.getTracks().forEach((t) => t.stop());
      audioCtx.close();
      setRecording(false);
      setProcessing(true);
      const blob = new Blob(chunksRef.current, { type: recorder.mimeType });
      const form = new FormData();
      form.append('audio', blob, 'audio.webm');
      try {
        const res = await fetch('/transcricao', { method: 'POST', body: form });
        if (!res.ok) throw new Error(await res.text());
        const { texto } = await res.json();
        setTranscricaoTexto(texto);
        setProcedureErro(null);
        try {
          const classRes = await fetch('/classificar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ texto, competencia: competenciaAtual() }),
          });
          if (!classRes.ok) throw new Error(await classRes.text());
          const { co_procedimento, no_procedimento, vl_total } = await classRes.json();
          setProcedure({
            descricao: no_procedimento,
            codigo: co_procedimento,
            valor: `R$ ${(vl_total / 100).toFixed(2).replace('.', ',')}`,
          });
        } catch {
          setProcedure(null);
          setProcedureErro('Falha ao classificar procedimento. Tente novamente.');
        }
        setStep(2);
      } catch {
        setTranscricaoErro('Falha na transcrição. Tente novamente.');
      } finally {
        setProcessing(false);
      }
    };
    mediaRecorderRef.current = recorder;
    recorder.start();
    setRecording(true);
  }

  async function handleConfirm() {
    setValidacaoLoading(true);
    setValidacaoResultado(null);
    setProcedureErro(null);
    try {
      const res = await fetch('/registros', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          co_procedimento: procedure.codigo,
          cnes: DEMO_PROFISSIONAL.cnes,
          cbo: DEMO_PROFISSIONAL.cbo,
          co_registro: '01',
          dt_atendimento: new Date().toISOString().split('T')[0],
          competencia: competenciaAtual(),
          cns: DEMO_PATIENT.cns.replace(/\s/g, ''),
          quantidade: 1,
          profissional_id: DEMO_PROFISSIONAL.id,
        }),
      });
      const data = res.status === 422 ? (await res.json()).detail : await res.json();
      setValidacaoResultado(data);
      if (data.aprovado) {
        setConfirmed(true);
        setTimeout(() => setBtnReady(true), 2000);
      }
    } catch (e) {
      setProcedureErro('Falha ao registrar procedimento. Tente novamente.');
    } finally {
      setValidacaoLoading(false);
    }
  }

  function handleConcluir() {
    setTimeout(() => setShowStats(true), 300);
  }

  // Adicionar procedimento ao mesmo paciente: salva o atual e volta ao step 1
  function handleAddProcedure() {
    if (procedure) {
      setProcedures((prev) => [...prev, {
        descricao: procedure.descricao,
        codigo: procedure.codigo,
        valor: procedure.valor,
      }]);
    }
    setProcedure(null);
    setTranscricaoTexto('');
    setConfirmed(false);
    setBtnReady(false);
    setProcessing(false);
    setShowStats(false);
    setTranscricaoErro(null);
    setProcedureErro(null);
    setValidacaoResultado(null);
    setStep(1);
  }

  function handleReset() {
    setStep(0); setScanning(false); setRecording(false); setProcessing(false);
    setConfirmed(false); setShowStats(false); setBtnReady(false);
    setTranscricaoTexto(''); setTranscricaoErro(null);
    setProcedure(null); setProcedureErro(null);
    setValidacaoResultado(null);
    setProcedures([]);
  }


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
            <span style={{ fontSize: 14, fontWeight: 700, color: BLUE }}>{DEMO_PROFISSIONAL.iniciais}</span>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: "#222" }}>{DEMO_PROFISSIONAL.nome}</div>
            <div style={{ fontSize: 11, color: GRAY_TEXT }}>{DEMO_PROFISSIONAL.especialidade} • {DEMO_PROFISSIONAL.estabelecimento}</div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: GREEN }}>{competenciaLabel()}</div>
            <div style={{ fontSize: 10, color: GRAY_TEXT }}>CNES {DEMO_PROFISSIONAL.cnes}</div>
          </div>
        </div>

        {/* CHAT */}
        <div ref={chatRef} style={{ flex: 1, overflowY: "auto", padding: "12px 12px 8px", display: "flex", flexDirection: "column" }}>

          {/* Step 0: identificação manual de paciente */}
          {step === 0 && !scanning && (
            <BotMessage>
              <div style={{ fontSize: 13, lineHeight: 1.5 }}>
                {`Olá, ${DEMO_PROFISSIONAL.nome.split(" ")[0]}! Escaneie o cartão SUS do paciente para começar o registro.`}
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

          {/* Paciente identificado (step >= 1) */}
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

          {/* Procedimentos já confirmados anteriormente (múltiplos procedimentos) */}
          {procedures.map((proc, idx) => (
            <BotMessage key={idx}>
              <div style={{ fontSize: 12, color: GRAY_TEXT, marginBottom: 4 }}>Procedimento {idx + 1} registrado</div>
              <CheckItem label="Procedimento" value={proc.descricao} />
              <CheckItem label={"C\u00F3digo"} value={proc.codigo} />
              <CheckItem label="Valor" value={proc.valor} />
              {proc.biopsia && <CheckItem label="Adicional" value={"Bi\u00F3psia de intestino grosso por endoscopia"} />}
            </BotMessage>
          ))}

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
              <span style={{ color: RED, fontSize: 13 }}>{transcricaoErro}</span>
            </BotMessage>
          )}

          {procedureErro && (
            <BotMessage>
              <span style={{ color: RED, fontSize: 13 }}>{procedureErro}</span>
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
              {procedure && <BotMessage>
                <div style={{ fontSize: 13, marginBottom: 8, fontWeight: 600, color: BLUE }}>
                  Procedimento identificado na SIGTAP
                </div>
                <CheckItem label="Procedimento" value={procedure.descricao} />
                <CheckItem label={"C\u00F3digo"} value={procedure.codigo} />
                <CheckItem label="Valor SIGTAP" value={procedure.valor} />
                {/* Botões Confirmar e Refazer */}
                <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                  <button
                    onClick={handleConfirm}
                    disabled={validacaoLoading || confirmed}
                    style={{ flex: 1, padding: "8px 0", borderRadius: 10, border: "none", background: validacaoLoading ? GRAY_TEXT : GREEN, color: "#fff", fontSize: 13, fontWeight: 700, cursor: validacaoLoading || confirmed ? "default" : "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 4, opacity: validacaoLoading || confirmed ? 0.7 : 1 }}
                  >
                    {validacaoLoading ? <Loader size={13} className="spin" /> : <Check size={13} strokeWidth={3} />}
                    {validacaoLoading ? 'Validando…' : 'Confirmar'}
                  </button>
                  <button
                    onClick={() => { setStep(1); setProcedure(null); setTranscricaoTexto(''); setProcedureErro(null); setTranscricaoErro(null); }}
                    style={{ flex: 1, padding: "8px 0", borderRadius: 10, border: "1px solid #DDD", background: "#fff", color: GRAY_TEXT, fontSize: 13, fontWeight: 600, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 4 }}
                  >
                    <RotateCcw size={13} /> Refazer
                  </button>
                </div>
              </BotMessage>
            </>
          )}

          {validacaoResultado && !validacaoResultado.aprovado && (
            <BotMessage>
              <div style={{ fontSize: 13, fontWeight: 700, color: RED, marginBottom: 8, display: "flex", alignItems: "center", gap: 5 }}>
                <X size={14} strokeWidth={3} /> Registro bloqueado — corrija os problemas abaixo
              </div>
              {validacaoResultado.bloqueios.map((g, i) => (
                <div key={i} style={{ background: "#FDEDEC", border: "1px solid #F5B7B1", borderRadius: 8, padding: "8px 10px", marginBottom: 6, fontSize: 12 }}>
                  <div style={{ fontWeight: 700, color: RED, marginBottom: 2 }}>{g.mensagem}</div>
                  <div style={{ color: "#922B21" }}>{g.detalhe}</div>
                </div>
              ))}
            </BotMessage>
          )}

          {validacaoResultado && validacaoResultado.aprovado && validacaoResultado.alertas.length > 0 && (
            <BotMessage>
              <div style={{ fontSize: 13, fontWeight: 700, color: "#B7950B", marginBottom: 8, display: "flex", alignItems: "center", gap: 5 }}>
                <AlertCircle size={14} /> Registro salvo com alertas para revisão
              </div>
              {validacaoResultado.alertas.map((a, i) => (
                <div key={i} style={{ background: "#FEFDE7", border: "1px solid #F9E79F", borderRadius: 8, padding: "8px 10px", marginBottom: 6, fontSize: 12 }}>
                  <div style={{ fontWeight: 700, color: "#9A7D0A", marginBottom: 2 }}>{a.mensagem}</div>
                  <div style={{ color: "#7D6608" }}>{a.detalhe}</div>
                </div>
              ))}
            </BotMessage>
          )}

          {confirmed && (
            <BotMessage>
              <div style={{ fontSize: 13, marginBottom: 6, fontWeight: 600, color: GREEN, display: "flex", alignItems: "center", gap: 5 }}>
                <Check size={14} strokeWidth={3} /> {"Todas as valida\u00E7\u00F5es aprovadas"}
              </div>
              <div style={{ fontSize: 12, marginBottom: 10 }}>
                <CheckItem label={"CBO compat\u00EDvel"} value="Sim" />
                <CheckItem label="CNES habilitado" value="Sim" />
                {validacaoResultado?.registro_id && (
                  <div style={{ fontSize: 11, color: GRAY_TEXT, marginTop: 4 }}>ID: {validacaoResultado.registro_id}</div>
                )}
              </div>

              <div style={{ background: GRAY_BG, borderRadius: 10, padding: 12, marginBottom: 10, border: "1px solid #E0E0E0" }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: BLUE, marginBottom: 8, textTransform: "uppercase", letterSpacing: 0.5 }}>
                  Resumo do registro
                </div>
                <div style={{ fontSize: 12, lineHeight: 1.8 }}>
                  <div><strong>Paciente:</strong> {DEMO_PATIENT.nome}</div>
                  <div><strong>CNS:</strong> {DEMO_PATIENT.cns}</div>
                  {procedures.map((proc, idx) => (
                    <div key={idx}><strong>Proc. {idx + 1}:</strong> {proc.descricao} ({proc.codigo})</div>
                  ))}
                  <div><strong>{procedures.length > 0 ? `Proc. ${procedures.length + 1}:` : "Procedimento:"}</strong> {procedure?.descricao} ({procedure?.codigo})</div>
                  <div><strong>Data:</strong> {new Date().toLocaleDateString('pt-BR')}</div>
                  <div><strong>Valor total:</strong> {procedure?.valor}</div>
                </div>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <div style={{
                  textAlign: "center", padding: "10px 0", color: GREEN, fontWeight: 700, fontSize: 14,
                  display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
                  animation: "fadeIn 0.4s ease",
                }}>
                  <Check size={18} strokeWidth={3} /> Registro salvo com sucesso!
                </div>
                {!showStats && (
                  <>
                    <button
                      onClick={handleAddProcedure}
                      style={{
                        width: "100%", padding: "10px 0", borderRadius: 12,
                        border: `1.5px solid ${BLUE}`, background: "#fff", color: BLUE,
                        fontSize: 13, fontWeight: 600, cursor: "pointer",
                        display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
                      }}
                    >
                      <Plus size={14} /> Adicionar procedimento
                    </button>
                    <button
                      onClick={handleConcluir}
                      style={{
                        width: "100%", padding: "10px 0", borderRadius: 12,
                        border: "none", background: BLUE, color: "#fff",
                        fontSize: 13, fontWeight: 600, cursor: "pointer",
                        display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
                      }}
                    >
                      <Check size={14} strokeWidth={3} /> Concluir atendimento
                    </button>
                  </>
                )}
              </div>
            </BotMessage>
          )}

          {showStats && (
            <BotMessage>
              <div style={{ fontSize: 12, color: GRAY_TEXT, marginBottom: 6 }}>
                Seu dia até agora:
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
                  label="Tempo médio"
                  bgColor={BLUE_LIGHT}
                  color={BLUE}
                />
              </div>
              <button
                onClick={handleReset}
                style={{
                  marginTop: 4, width: "100%", padding: "10px 0", borderRadius: 10,
                  border: `1.5px solid ${BLUE}`, background: "#fff", color: BLUE,
                  fontSize: 13, fontWeight: 600, cursor: "pointer",
                }}
              >
                Registrar próximo paciente
              </button>
            </BotMessage>
          )}
        </div>

        {/* TEXT INPUT */}
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
            width: 38, height: 38, borderRadius: "50%", border: "none",
            background: BLUE, cursor: "pointer",
            display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
          }}>
            <ArrowUp size={18} color="#fff" strokeWidth={2.5} />
          </button>
        </div>

        {/* MAIN ACTION BUTTONS */}
        {step === 0 ? (
          // Step 0: dois botões (escanear + gravar)
          <>
            <div style={{ display: "flex", gap: 10, padding: "6px 12px 0", background: "#fff", flexShrink: 0 }}>
              <button
                className="action-btn"
                onClick={handleScan}
                style={{
                  flex: 1, height: 80, borderRadius: 18, border: "none",
                  cursor: scanning ? "default" : "pointer",
                  background: scanning ? "#FFF3CD" : BLUE_LIGHT,
                  display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6,
                }}
              >
                {scanning
                  ? <Loader size={28} color="#B7950B" strokeWidth={2} style={{ animation: "pulse 1s ease infinite" }} />
                  : <Camera size={28} color={BLUE} strokeWidth={1.8} />
                }
                <span style={{ fontSize: 13, fontWeight: 600, color: scanning ? "#B7950B" : BLUE }}>
                  {scanning ? "Escaneando..." : "Escanear cart\u00E3o"}
                </span>
              </button>

              <button
                className="action-btn"
                style={{
                  flex: 1, height: 80, borderRadius: 18, border: "none",
                  cursor: "default",
                  background: "#F0F0F0",
                  display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6,
                  opacity: 0.35,
                }}
              >
                <Mic size={28} color="#999" strokeWidth={1.8} />
                <span style={{ fontSize: 13, fontWeight: 600, color: "#999" }}>Gravar procedimento</span>
              </button>
            </div>
            <div style={{ background: "#fff", padding: "6px 12px 14px", display: "flex", justifyContent: "center", gap: 24, flexShrink: 0 }}>
              <button onClick={() => setInputMode("cpf")} style={{ background: "none", border: "none", color: GRAY_TEXT, fontSize: 12, cursor: "pointer", textDecoration: "underline" }}>
                Digitar CPF
              </button>
              <button onClick={() => setInputMode("cns")} style={{ background: "none", border: "none", color: GRAY_TEXT, fontSize: 12, cursor: "pointer", textDecoration: "underline" }}>
                Digitar CNS
              </button>
            </div>
          </>
        ) : (
          // Step >= 1: botão de microfone centralizado com estados: gravando / processando / ok→mic
          <div style={{ padding: "6px 12px 14px", background: "#fff", flexShrink: 0 }}>
            {(() => {
              // Após confirmação: 2s mostra "Procedimento OK", depois volta ao mic
              if (confirmed && !btnReady) {
                return (
                  <button className="action-btn" style={{ width: "100%", height: 80, borderRadius: 18, border: "none", cursor: "default", background: GREEN_LIGHT, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6 }}>
                    <Check size={28} color={GREEN} strokeWidth={2.5} />
                    <span style={{ fontSize: 13, fontWeight: 600, color: GREEN }}>Procedimento OK</span>
                  </button>
                );
              }
              if (confirmed && btnReady) {
                return (
                  <button className="action-btn" onClick={handleAddProcedure} style={{ width: "100%", height: 80, borderRadius: 18, border: "none", cursor: "pointer", background: BLUE_LIGHT, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6, animation: "fadeIn 0.4s ease" }}>
                    <Mic size={28} color={BLUE} strokeWidth={1.8} />
                    <span style={{ fontSize: 13, fontWeight: 600, color: BLUE }}>Gravar procedimento</span>
                  </button>
                );
              }
              if (processing) {
                return (
                  <button className="action-btn" style={{ width: "100%", height: 80, borderRadius: 18, border: "none", cursor: "default", background: "#FFF8E7", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6 }}>
                    <Loader size={28} color="#B7950B" strokeWidth={2} style={{ animation: "pulse 1s ease infinite" }} />
                    <span style={{ fontSize: 13, fontWeight: 600, color: "#B7950B" }}>Processando...</span>
                  </button>
                );
              }
              if (recording) {
                return (
                  <button className="action-btn" onClick={stopRecording} style={{ width: "100%", height: 80, borderRadius: 18, border: "none", cursor: "pointer", background: "#FADBD8", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6, animation: "rec 1.5s ease infinite" }}>
                    <Circle size={28} color={RED} fill={RED} strokeWidth={0} />
                    <span style={{ fontSize: 13, fontWeight: 600, color: RED }}>Gravando...</span>
                  </button>
                );
              }
              // step 1, idle
              return (
                <button className="action-btn" onClick={handleMic} style={{ width: "100%", height: 80, borderRadius: 18, border: "none", cursor: step === 1 ? "pointer" : "default", background: step === 1 ? BLUE_LIGHT : "#F0F0F0", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6, opacity: step > 1 ? 0.5 : 1 }}>
                  <Mic size={28} color={step === 1 ? BLUE : "#999"} strokeWidth={1.8} />
                  <span style={{ fontSize: 13, fontWeight: 600, color: step === 1 ? BLUE : "#999" }}>Gravar procedimento</span>
                </button>
              );
            })()}
          </div>
        )}

        {step > 0 && step < 1 && <div style={{ background: "#fff", height: 14, flexShrink: 0 }} />}
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
