import { useEffect, useState } from "react";
import { Download, FileCheck2, FileUp, Send, UserRound } from "lucide-react";

import {
  downloadOwnApplicationDocument,
  getOwnApplication,
  getApiErrorMessage,
  submitOwnApplication,
  updateOwnApplicant,
  updateOwnApplication,
  uploadOwnApplicationDocument,
  type ApplicationDetailResponse,
} from "./operationalApi";

/** Render the authenticated applicant's bound application and private document workflow. */
export default function ApplicantPortal() {
  const [detail, setDetail] = useState<ApplicationDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  /** Reload authoritative applicant, application, and document state. */
  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      setDetail(await getOwnApplication());
    } catch (requestError) {
      setError(getApiErrorMessage(requestError));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, []);

  /** Run one mutation with consistent feedback and authoritative refresh. */
  const mutate = async (action: () => Promise<unknown>, success: string) => {
    setWorking(true);
    setError(null);
    setNotice(null);
    try {
      await action();
      setNotice(success);
      await load();
    } catch (requestError) {
      setError(getApiErrorMessage(requestError));
    } finally {
      setWorking(false);
    }
  };

  if (loading && !detail) return <section className="state-panel" aria-live="polite">Loading your application...</section>;
  if (error && !detail) return <section className="state-panel error-state"><p>{error}</p><button type="button" onClick={() => void load()}>Retry</button></section>;
  if (!detail) return <section className="state-panel">No application is linked to this account.</section>;

  const editable = detail.application.state === "draft";
  /** Download authorized media using a short-lived browser object URL. */
  const download = async (documentId: string, filename: string) => {
    try {
      const blob = await downloadOwnApplicationDocument(documentId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(url);
    } catch (requestError) {
      setError(getApiErrorMessage(requestError));
    }
  };
  return (
    <div className="module-page applicant-portal">
      <header className="module-heading"><div><p>APPLICANT WORKSPACE</p><h1>My application</h1><span>Track your application and submit required documents.</span></div><strong className="status-pill">{detail.application.state.replaceAll("_", " ")}</strong></header>
      {notice && <div className="feedback success-feedback" role="status">{notice}</div>}
      {error && <div className="feedback error-feedback" role="alert">{error}</div>}
      <section className="operational-grid applicant-grid">
        <article className="operations-panel"><header><div><UserRound aria-hidden /><h2>Applicant details</h2></div><span>{detail.application.application_number}</span></header><form onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); void mutate(() => updateOwnApplicant({ first_name: String(form.get("first_name")), last_name: String(form.get("last_name")), email: String(form.get("email")), mobile_number: String(form.get("mobile_number")), date_of_birth: String(form.get("date_of_birth")) }), "Applicant details saved."); }}><div className="form-grid"><label>First name<input name="first_name" defaultValue={detail.applicant.first_name} disabled={!editable || working} required /></label><label>Last name<input name="last_name" defaultValue={detail.applicant.last_name} disabled={!editable || working} required /></label><label>Email<input name="email" type="email" defaultValue={detail.applicant.email ?? ""} disabled={!editable || working} required /></label><label>Mobile number<input name="mobile_number" defaultValue={detail.applicant.mobile_number ?? ""} disabled={!editable || working} required /></label><label>Date of birth<input name="date_of_birth" type="date" defaultValue={detail.applicant.date_of_birth ?? ""} disabled={!editable || working} required /></label></div>{editable && <button className="primary-action" type="submit" disabled={working}>Save details</button>}</form></article>
        <article className="operations-panel"><header><div><FileCheck2 aria-hidden /><h2>Application statement</h2></div><span>{detail.application.submitted_at ? new Date(detail.application.submitted_at).toLocaleDateString() : "Not submitted"}</span></header><form onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); void mutate(() => updateOwnApplication(String(form.get("remarks"))), "Application statement saved."); }}><label>Statement<textarea name="remarks" defaultValue={detail.application.remarks ?? ""} disabled={!editable || working} rows={7} /></label>{editable && <div className="inline-actions"><button className="row-action secondary" type="submit" disabled={working}>Save statement</button><button className="primary-action" type="button" disabled={working} onClick={() => void mutate(submitOwnApplication, "Application submitted for review.")}><Send aria-hidden /> Submit application</button></div>}</form></article>
      </section>
      <section className="operations-panel"><header><div><FileUp aria-hidden /><h2>Documents</h2></div><span>{detail.documents.length} submitted</span></header>{editable && <form className="applicant-upload" onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); const file = form.get("file"); if (!(file instanceof File) || file.size === 0) { setError("Choose a PDF, JPEG, or PNG file."); return; } void mutate(() => uploadOwnApplicationDocument({ documentType: String(form.get("document_type")), documentNumber: String(form.get("document_number")), file }), "Document uploaded privately."); }}><div className="form-grid"><label>Document type<select name="document_type" disabled={working} required><option value="identity">Identity proof</option><option value="marksheet">Mark sheet</option><option value="community">Community certificate</option><option value="transfer">Transfer certificate</option></select></label><label>Document number<input name="document_number" disabled={working} /></label><label>File<input name="file" type="file" accept="application/pdf,image/jpeg,image/png" disabled={working} required /></label></div><button className="primary-action" type="submit" disabled={working}><FileUp aria-hidden /> Upload document</button></form>}{detail.documents.length === 0 ? <p className="empty-copy">No documents submitted yet.</p> : <div className="record-list">{detail.documents.map((document) => <article key={document.id}><div><strong>{document.document_type.replaceAll("_", " ")}</strong><p>{document.document_number || "No document number"}</p></div><span className="status-pill">{document.verification_state}</span>{document.media_object_id && <button className="icon-button" type="button" aria-label={`Download ${document.document_type}`} onClick={() => void download(document.id, `${document.document_type}.pdf`)}><Download aria-hidden /></button>}</article>)}</div>}</section>
    </div>
  );
}