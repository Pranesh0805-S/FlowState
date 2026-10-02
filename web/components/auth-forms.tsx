"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import { ArrowRight, Check, CheckCheck, LoaderCircle } from "@/components/icons";

function Brand() {
  return <Link href="/" className="brand auth-brand"><span className="brand-mark"><CheckCheck size={17}/></span><span>flowstate<span className="brand-period">.</span></span></Link>;
}
function AuthScaffold({ children, footer = true }: { children: React.ReactNode; footer?: boolean }) {
  return <main className="auth-wrap"><section className="auth-story"><Brand/><div className="auth-story-copy"><div className="eyebrow auth-eyebrow">A clearer way to get there</div><h1>Make space for your <em>best work.</em></h1><p>Bring your plans, priorities, and people into one calm workspace. Then take the next right step.</p><div className="auth-benefits"><span><Check size={14}/> Everything in one place</span><span><Check size={14}/> Built for focus</span></div></div>{footer && <div className="auth-story-foot">© {new Date().getFullYear()} Flowstate · Thoughtful work, well done.</div>}</section><section className="auth-panel"><div className="auth-card">{children}</div></section></main>;
}
function ErrorMessage({ children }: { children: string }) { return children ? <div className="message message-error" role="alert">{children}</div> : null; }

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setBusy(true);
    try { await api("auth/login", { method: "POST", body: JSON.stringify({ email, password }) }); router.replace("/dashboard"); }
    catch (e) { setError(e instanceof Error ? e.message : "Could not sign in"); }
    finally { setBusy(false); }
  }
  return <AuthScaffold><div className="form-kicker">WELCOME BACK</div><h2>Good to see you.</h2><p>Sign in to pick up where you left off.</p><form className="auth-form" onSubmit={submit}>
    <div className="field"><label htmlFor="email">Email address</label><input id="email" type="email" autoComplete="email" placeholder="you@example.com" required value={email} onChange={e=>setEmail(e.target.value)}/></div>
    <div className="field"><div className="label-row"><label htmlFor="password">Password</label><Link className="link small-link" href="/forgot-password">Forgot password?</Link></div><input id="password" type="password" autoComplete="current-password" placeholder="Enter your password" required value={password} onChange={e=>setPassword(e.target.value)}/></div>
    <ErrorMessage>{error}</ErrorMessage><button className="btn auth-submit" disabled={busy}>{busy ? <LoaderCircle className="spin" size={17}/> : <>Sign in <ArrowRight size={16}/></>}</button>
  </form><div className="auth-links">New to Flowstate? <Link href="/register" className="link">Create an account</Link></div><div className="auth-note">Your workspace is private and secure.</div></AuthScaffold>;
}

export function RegisterForm() {
  const router = useRouter();
  const [step, setStep] = useState<1|2|3>(1);
  const [name,setName]=useState(""); const [email,setEmail]=useState(""); const [otp,setOtp]=useState("");
  const [password,setPassword]=useState(""); const [confirm,setConfirm]=useState(""); const [error,setError]=useState(""); const [success,setSuccess]=useState(""); const [busy,setBusy]=useState(false);
  async function sendCode(event: React.FormEvent<HTMLFormElement>) { event.preventDefault();setError("");setSuccess("");setBusy(true);try{await api("auth/register",{method:"POST",body:JSON.stringify({name,email})});setSuccess("We sent a six-digit code to your email.");setStep(2);}catch(e){setError(e instanceof Error?e.message:"Could not send a verification code");}finally{setBusy(false);} }
  async function verify(event: React.FormEvent<HTMLFormElement>) { event.preventDefault();setError("");setBusy(true);try{await api("auth/register/verify",{method:"POST",body:JSON.stringify({email,otp})});setSuccess("Email verified. You’re nearly there.");setStep(3);}catch(e){setError(e instanceof Error?e.message:"That code could not be verified");}finally{setBusy(false);} }
  async function finish(event: React.FormEvent<HTMLFormElement>) { event.preventDefault();setError("");if(password!==confirm){setError("Your passwords don’t match.");return;}setBusy(true);try{await api("auth/register/complete",{method:"POST",body:JSON.stringify({email,password})});await api("auth/login",{method:"POST",body:JSON.stringify({email,password})});router.replace("/dashboard");}catch(e){setError(e instanceof Error?e.message:"Could not finish creating your account");}finally{setBusy(false);} }
  const steps=["Your details","Verify email","Create password"];
  return <AuthScaffold><div className="form-kicker">YOUR WORKSPACE STARTS HERE</div><h2>Create your account.</h2><p>Set up your personal space in just a moment.</p><div className="stepper">{steps.map((item,index)=><div key={item} className={`step ${step===index+1?"step-current":""} ${step>index+1?"step-done":""}`}><span>{step>index+1?<Check size={12}/>:index+1}</span>{item}</div>)}</div>
    {step===1&&<form className="auth-form" onSubmit={sendCode}><div className="field"><label htmlFor="name">Your name</label><input id="name" autoComplete="name" placeholder="What should we call you?" required maxLength={120} value={name} onChange={e=>setName(e.target.value)}/></div><div className="field"><label htmlFor="reg-email">Email address</label><input id="reg-email" type="email" autoComplete="email" placeholder="you@example.com" required value={email} onChange={e=>setEmail(e.target.value)}/></div><ErrorMessage>{error}</ErrorMessage>{success&&<div className="message message-success">{success}</div>}<button className="btn auth-submit" disabled={busy}>{busy?<LoaderCircle className="spin" size={17}/>:<>Continue <ArrowRight size={16}/></>}</button></form>}
    {step===2&&<form className="auth-form" onSubmit={verify}><div className="verify-email-note">Code sent to <strong>{email}</strong></div><div className="field"><label htmlFor="otp">Six-digit verification code</label><input id="otp" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} placeholder="000000" required value={otp} onChange={e=>setOtp(e.target.value.replace(/\D/g,"").slice(0,6))}/></div><ErrorMessage>{error}</ErrorMessage>{success&&<div className="message message-success">{success}</div>}<button className="btn auth-submit" disabled={busy}>{busy?<LoaderCircle className="spin" size={17}/>:<>Verify email <ArrowRight size={16}/></>}</button><button type="button" className="text-button" onClick={()=>setStep(1)}>Change email address</button></form>}
    {step===3&&<form className="auth-form" onSubmit={finish}><div className="verified-banner"><span className="verified-check"><Check size={14}/></span> Email verified <span>{email}</span></div><div className="field"><label htmlFor="reg-password">Create password</label><input id="reg-password" type="password" autoComplete="new-password" minLength={8} maxLength={128} placeholder="At least 8 characters" required value={password} onChange={e=>setPassword(e.target.value)}/></div><div className="field"><label htmlFor="confirm-password">Confirm password</label><input id="confirm-password" type="password" autoComplete="new-password" required value={confirm} onChange={e=>setConfirm(e.target.value)}/></div><ErrorMessage>{error}</ErrorMessage><button className="btn auth-submit" disabled={busy}>{busy?<LoaderCircle className="spin" size={17}/>:<>Create my account <ArrowRight size={16}/></>}</button></form>}
    <div className="auth-links">Already have a Flowstate account? <Link href="/login" className="link">Sign in</Link></div></AuthScaffold>;
}

export function ForgotPasswordForm() {
  const router=useRouter();const [email,setEmail]=useState("");const [otp,setOtp]=useState("");const [step,setStep]=useState<1|2>(1);const [password,setPassword]=useState("");const [confirm,setConfirm]=useState("");const [error,setError]=useState("");const [ok,setOk]=useState("");const [busy,setBusy]=useState(false);
  async function request(event:React.FormEvent<HTMLFormElement>){event.preventDefault();setError("");setOk("");setBusy(true);try{await api("auth/password-reset",{method:"POST",body:JSON.stringify({email})});setOk("A verification code is on its way.");setStep(2);}catch(e){setError(e instanceof Error?e.message:"Could not send your code");}finally{setBusy(false);}}
  async function verify(event:React.FormEvent<HTMLFormElement>){event.preventDefault();setError("");setBusy(true);try{await api("auth/password-reset/verify",{method:"POST",body:JSON.stringify({email,otp})});await api("auth/password-reset/complete",{method:"POST",body:JSON.stringify({email,new_password:password})});setOk("Password changed. Sign in with your new password.");setTimeout(()=>router.replace("/login"),1300);}catch(e){setError(e instanceof Error?e.message:"Could not verify code");}finally{setBusy(false);}}
  return <AuthScaffold footer={false}><div className="form-kicker">ACCOUNT RECOVERY</div><h2>Reset your password.</h2><p>We’ll verify your email before making any changes.</p>{step===1?<form className="auth-form" onSubmit={request}><div className="field"><label htmlFor="reset-email">Email address</label><input id="reset-email" type="email" autoComplete="email" required placeholder="you@example.com" value={email} onChange={e=>setEmail(e.target.value)}/></div><ErrorMessage>{error}</ErrorMessage>{ok&&<div className="message message-success">{ok}</div>}<button className="btn auth-submit" disabled={busy}>{busy?<LoaderCircle className="spin" size={17}/>:<>Send verification code <ArrowRight size={16}/></>}</button></form>:<form className="auth-form" onSubmit={verify}><div className="verify-email-note">Verification code sent to <strong>{email}</strong></div><div className="field"><label htmlFor="reset-otp">Verification code</label><input id="reset-otp" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} required placeholder="000000" value={otp} onChange={e=>setOtp(e.target.value.replace(/\D/g,"").slice(0,6))}/></div><div className="field"><label htmlFor="new-password">New password</label><input id="new-password" type="password" autoComplete="new-password" minLength={8} required value={password} onChange={e=>setPassword(e.target.value)}/></div><div className="field"><label htmlFor="new-confirm">Confirm new password</label><input id="new-confirm" type="password" autoComplete="new-password" required value={confirm} onChange={e=>setConfirm(e.target.value)}/></div>{password!==confirm&&confirm&&<ErrorMessage>Passwords don’t match.</ErrorMessage>}<ErrorMessage>{error}</ErrorMessage>{ok&&<div className="message message-success">{ok}</div>}<button className="btn auth-submit" disabled={busy||password!==confirm}>{busy?<LoaderCircle className="spin" size={17}/>:<>Set new password <ArrowRight size={16}/></>}</button></form>}<div className="auth-links"><Link href="/login" className="link">Back to sign in</Link></div></AuthScaffold>;
}
