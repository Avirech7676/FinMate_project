import { useState, useCallback, useContext } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { AuthContext } from '../AuthContext';
import { API_URL } from '../apiConfig';
import { UploadCloud, FileText, CheckCircle, Zap, X, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface Props {
  onSuccess?: () => void;
}

type CsvPreview = {
  status: string;
  columns: string[];
  detected: {
    date_column: string | null;
    description_column: string | null;
    amount_column: string | null;
    debit_column: string | null;
    credit_column: string | null;
    currency_column: string | null;
    source_currency: string | null;
  };
  sample_rows: Array<{
    date: string | null;
    description: string | null;
    amount_raw: string | null;
  }>;
};

const SUPPORTED_SOURCE_CURRENCIES = ['USD', 'INR', 'EUR', 'GBP'];

type ReceiptPreview = {
  receipt_id: number;
  data: {
    amount?: number;
    merchant?: string;
    category?: string;
    date?: string;
    description?: string;
  };
  status: string;
};

export default function DataImport({ onSuccess }: Props) {
  const auth = useContext(AuthContext);
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [csvPreview, setCsvPreview] = useState<CsvPreview | null>(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [sourceCurrency, setSourceCurrency] = useState<string>('USD');
  const [customCurrency, setCustomCurrency] = useState<string>('');
  const [receiptPreview, setReceiptPreview] = useState<ReceiptPreview | null>(null);
  const [showReceiptModal, setShowReceiptModal] = useState(false);
  const [receiptAmount, setReceiptAmount] = useState<string>('');
  const [receiptDescription, setReceiptDescription] = useState<string>('');
  const [receiptCategory, setReceiptCategory] = useState<string>('uncategorized');

  const resolvedSourceCurrency = SUPPORTED_SOURCE_CURRENCIES.includes(sourceCurrency)
    ? sourceCurrency
    : customCurrency || 'USD';

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (!acceptedFiles || acceptedFiles.length === 0) return;
    const file = acceptedFiles[0];
    
    setLoading(true);
    setSuccessMsg('');
    setErrorMsg('');

    try {
      if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
        // STEP 1: Ask backend for a preview / column mapping before importing
        const previewForm = new FormData();
        previewForm.append('file', file);

        try {
          const previewRes = await axios.post<CsvPreview>(`${API_URL}/upload-csv/preview`, previewForm, {
            headers: {
              'Content-Type': 'multipart/form-data',
              Authorization: `Bearer ${auth?.token}`
            }
          });

          setPendingFile(file);
          setCsvPreview(previewRes.data);

          // Pre-select currency: backend guess → user profile currency → USD
          const detectedCurrency = previewRes.data.detected?.source_currency || auth?.user?.currency || 'USD';
          const upper = detectedCurrency.toUpperCase();
          if (SUPPORTED_SOURCE_CURRENCIES.includes(upper)) {
            setSourceCurrency(upper);
            setCustomCurrency('');
          } else {
            setSourceCurrency('OTHER');
            setCustomCurrency(upper);
          }

          setShowConfirmModal(true);
        } catch (previewErr: any) {
          setErrorMsg(previewErr.response?.data?.detail || 'Could not analyze CSV. Please check the file format.');
        } finally {
          setLoading(false);
        }
      } else if (file.type.startsWith('image/')) {
        const formData = new FormData();
        formData.append('file', file);

        // Use OCR + confirmation workflow
        const res = await axios.post<ReceiptPreview>(`${API_URL}/receipts/scan-and-confirm`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
            Authorization: `Bearer ${auth?.token}`
          }
        });

        const preview = res.data;
        setReceiptPreview(preview);
        const amountVal = preview.data.amount ?? 0;
        setReceiptAmount(amountVal ? String(amountVal) : '');
        const rawDescription =
          preview.data.description ||
          preview.data.merchant ||
          'Receipt transaction';
        setReceiptDescription(rawDescription);
        setReceiptCategory((preview.data.category || 'uncategorized').toLowerCase());
        setShowReceiptModal(true);
      } else {
        setErrorMsg("Unsupported file type. Please upload a CSV or an Image receipt.");
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || "Upload failed. Please try again.");
    } finally {
      // For CSVs we keep `loading` state controlled around the preview/import flow.
      // For receipts, loading is cleared when the modal is shown.
      if (!(file.type === 'text/csv' || file.name.endsWith('.csv'))) {
        setLoading(false);
      }
    }
  }, [auth]);

  const handleConfirmImport = async () => {
    if (!pendingFile) return;
    setLoading(true);
    setSuccessMsg('');
    setErrorMsg('');

    const formData = new FormData();
    formData.append('file', pendingFile);
    formData.append('source_currency', resolvedSourceCurrency);

    try {
      const res = await axios.post(`${API_URL}/upload-csv`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          Authorization: `Bearer ${auth?.token}`
        }
      });
      setSuccessMsg(`Successfully imported ${res.data.imported} transactions from CSV.`);
      setShowConfirmModal(false);
      setPendingFile(null);
      setCsvPreview(null);
      onSuccess?.();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || "CSV import failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleCancelImport = () => {
    setShowConfirmModal(false);
    setPendingFile(null);
    setCsvPreview(null);
  };

  const handleConfirmReceipt = async () => {
    if (!receiptPreview) return;
    setLoading(true);
    setSuccessMsg('');
    setErrorMsg('');

    const parsedAmount = parseFloat(receiptAmount || '0');

    try {
      await axios.post(
        `${API_URL}/receipts/${receiptPreview.receipt_id}/confirm`,
        {
          receipt_id: receiptPreview.receipt_id,
          confirmed: true,
          amount: isNaN(parsedAmount) ? undefined : parsedAmount,
          description: receiptDescription || undefined,
          category: receiptCategory || undefined
        },
        {
          headers: {
            Authorization: `Bearer ${auth?.token}`
          }
        }
      );
      setSuccessMsg('Receipt confirmed and transaction created.');
      setShowReceiptModal(false);
      setReceiptPreview(null);
      onSuccess?.();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to confirm receipt. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRejectReceipt = async () => {
    if (!receiptPreview) {
      setShowReceiptModal(false);
      return;
    }
    try {
      await axios.post(
        `${API_URL}/receipts/${receiptPreview.receipt_id}/confirm`,
        {
          receipt_id: receiptPreview.receipt_id,
          confirmed: false
        },
        {
          headers: {
            Authorization: `Bearer ${auth?.token}`
          }
        }
      );
    } catch {
      // best-effort; ignoring errors on rejection
    } finally {
      setShowReceiptModal(false);
      setReceiptPreview(null);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'image/*': ['.jpeg', '.jpg', '.png', '.webp']
    },
    maxFiles: 1
  });

  return (
    <div className="w-full max-w-2xl mx-auto my-8 p-6 glass-card relative">
        {/* Decorative corner glow */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-[--color-accent-green] opacity-[0.15] blur-3xl rounded-full"></div>

        <h3 className="text-xl font-semibold mb-1 flex items-center gap-2">
            <Zap className="w-5 h-5 text-[--color-accent-green]" />
            Smart Import
        </h3>
        <p className="text-[--color-text-secondary] text-sm mb-6">
            Drag & Drop a bank CSV to import history, or drop a receipt photo for Gemini AI scanning.
        </p>

        <div 
          {...getRootProps()} 
          className={`
            border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-300
            ${isDragActive ? 'border-[--color-accent-green] bg-[--color-accent-green-glow]' : 'border-white/10 hover:border-white/30 hover:bg-white/[0.02]'}
          `}
        >
          <input {...getInputProps()} />
          
          <div className="flex flex-col items-center justify-center pointer-events-none">
            {isDragActive ? (
              <UploadCloud className="w-12 h-12 text-[--color-accent-green] animate-bounce mb-4" />
            ) : (
              <FileText className="w-12 h-12 text-[--color-text-muted] mb-4" />
            )}
            
            <p className="text-lg font-medium">
              {isDragActive ? "Drop to upload instantly" : "Click or drag files here"}
            </p>
            <p className="text-sm text-[--color-text-secondary] mt-2">
              Supports CSV, JPG, PNG up to 10MB
            </p>
          </div>
        </div>

        <AnimatePresence>
            {loading && (
                <motion.div 
                    initial={{ opacity: 0, height: 0 }} 
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-4 p-4 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center"
                >
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-[--color-accent-green] mr-3"></div>
                    <span className="text-sm text-[--color-text-secondary]">Processing with FinMate Engine...</span>
                </motion.div>
            )}

            {successMsg && (
                <motion.div 
                    initial={{ opacity: 0, scale: 0.95 }} 
                    animate={{ opacity: 1, scale: 1 }}
                    className="mt-4 p-4 rounded-lg bg-[--color-accent-green-glow] border border-[--color-accent-green]/30 flex items-start gap-3"
                >
                    <CheckCircle className="w-5 h-5 text-[--color-accent-green] mt-0.5" />
                    <p className="text-sm text-[--color-accent-green]">{successMsg}</p>
                </motion.div>
            )}
            
            {errorMsg && (
                <motion.div 
                    initial={{ opacity: 0, scale: 0.95 }} 
                    animate={{ opacity: 1, scale: 1 }}
                    className="mt-4 p-4 rounded-lg bg-[--color-accent-red-glow] border border-[--color-accent-red]/30 flex items-start gap-3"
                >
                    <p className="text-sm text-[--color-accent-red]">{errorMsg}</p>
                </motion.div>
            )}

            {/* CSV Confirmation Modal */}
            {showConfirmModal && csvPreview && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
              >
                <motion.div
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.9, opacity: 0 }}
                  className="max-w-xl w-full mx-4 p-6 rounded-2xl border border-white/10 bg-[#050814] shadow-2xl relative"
                >
                  <button
                    onClick={handleCancelImport}
                    className="absolute top-4 right-4 text-gray-400 hover:text-white"
                    aria-label="Close"
                  >
                    <X className="w-5 h-5" />
                  </button>

                  <h3 className="text-lg font-semibold mb-1">Confirm CSV Mapping</h3>
                  <p className="text-xs text-[--color-text-secondary] mb-4">
                    We analyzed the file and guessed the right columns. Please confirm before importing.
                  </p>

                  {/* Column mapping summary */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4 text-xs">
                    <div className="bg-white/5 rounded-lg p-3 border border-white/10">
                      <p className="font-semibold text-[--color-text-secondary] mb-1">Detected columns</p>
                      <ul className="space-y-1">
                        <li><span className="text-gray-400">Date:</span> {csvPreview.detected.date_column || <span className="text-[--color-accent-red]">Not found</span>}</li>
                        <li><span className="text-gray-400">Description:</span> {csvPreview.detected.description_column || <span className="text-[--color-accent-red]">Not found</span>}</li>
                        <li><span className="text-gray-400">Amount:</span> {csvPreview.detected.amount_column || '—'}</li>
                        <li><span className="text-gray-400">Debit:</span> {csvPreview.detected.debit_column || '—'}</li>
                        <li><span className="text-gray-400">Credit:</span> {csvPreview.detected.credit_column || '—'}</li>
                      </ul>
                    </div>
                    <div className="bg-white/5 rounded-lg p-3 border border-white/10">
                      <p className="font-semibold text-[--color-text-secondary] mb-1">All headers</p>
                      <p className="text-[10px] text-gray-400 break-words">
                        {csvPreview.columns.join(', ')}
                      </p>
                    </div>
                  </div>

                  {/* Sample rows */}
                  <div className="mb-4">
                    <p className="text-xs font-semibold text-[--color-text-secondary] mb-2">Sample rows</p>
                    <div className="bg-black/30 rounded-lg border border-white/10 max-h-32 overflow-auto text-xs">
                      {csvPreview.sample_rows.map((row, idx) => (
                        <div
                          key={idx}
                          className="px-3 py-2 border-b border-white/5 last:border-b-0 flex gap-3"
                        >
                          <span className="text-gray-500 w-6 shrink-0">{idx + 1}.</span>
                          <span className="text-gray-300 flex-1 truncate">{row.date || '—'}</span>
                          <span className="text-gray-400 flex-1 truncate">{row.description || '—'}</span>
                          <span className="text-gray-200 w-24 text-right truncate">{row.amount_raw || '—'}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Currency confirmation */}
                  <div className="mb-4">
                    <p className="text-xs font-semibold text-[--color-text-secondary] mb-1">
                      What currency are these amounts in?
                    </p>
                    <div className="flex flex-wrap items-center gap-2">
                      <select
                        value={sourceCurrency}
                        onChange={(e) => setSourceCurrency(e.target.value)}
                        className="bg-black/40 border border-white/20 rounded-md px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-cyan-500"
                      >
                        {SUPPORTED_SOURCE_CURRENCIES.map((c) => (
                          <option key={c} value={c}>{c}</option>
                        ))}
                        <option value="OTHER">Other…</option>
                      </select>
                      {sourceCurrency === 'OTHER' && (
                        <input
                          type="text"
                          value={customCurrency}
                          onChange={(e) => setCustomCurrency(e.target.value.toUpperCase())}
                          placeholder="e.g. AUD"
                          className="bg-black/40 border border-white/20 rounded-md px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-cyan-500"
                        />
                      )}
                    </div>
                    <div className="mt-2 flex items-start gap-1 text-[10px] text-[--color-text-secondary]">
                      <AlertCircle className="w-3 h-3 mt-0.5" />
                      <p>
                        We&apos;ll convert from this source currency into your profile currency ({auth?.user?.currency_symbol || '$'}).
                      </p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="mt-5 flex flex-col sm:flex-row gap-2">
                    <button
                      type="button"
                      onClick={handleConfirmImport}
                      disabled={loading}
                      className="flex-1 px-4 py-2 bg-gradient-to-r from-[--color-accent-green] to-[--color-accent-blue] rounded-md text-sm font-semibold hover:opacity-90 disabled:opacity-50"
                    >
                      {loading ? 'Importing…' : 'Confirm & Import'}
                    </button>
                    <button
                      type="button"
                      onClick={handleCancelImport}
                      className="flex-1 px-4 py-2 bg-white/5 border border-white/10 rounded-md text-sm text-[--color-text-secondary] hover:bg-white/10"
                    >
                      Cancel
                    </button>
                  </div>
                </motion.div>
              </motion.div>
            )}

            {/* Receipt OCR Confirmation Modal */}
            {showReceiptModal && receiptPreview && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
              >
                <motion.div
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.9, opacity: 0 }}
                  className="max-w-md w-full mx-4 p-6 rounded-2xl border border-white/10 bg-[#050814] shadow-2xl relative"
                >
                  <button
                    onClick={handleRejectReceipt}
                    className="absolute top-4 right-4 text-gray-400 hover:text-white"
                    aria-label="Close"
                  >
                    <X className="w-5 h-5" />
                  </button>

                  <h3 className="text-lg font-semibold mb-1">Confirm Receipt Details</h3>
                  <p className="text-xs text-[--color-text-secondary] mb-4">
                    We used OCR to read your receipt. Adjust any fields below before creating a transaction.
                  </p>

                  <div className="space-y-3 text-xs">
                    <div>
                      <label className="block text-[--color-text-secondary] mb-1">
                        Amount ({auth?.user?.currency_symbol || '$'})
                      </label>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={receiptAmount}
                        onChange={(e) => setReceiptAmount(e.target.value)}
                        className="w-full bg-black/40 border border-white/20 rounded-md px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-cyan-500"
                      />
                    </div>

                    <div>
                      <label className="block text-[--color-text-secondary] mb-1">
                        Description
                      </label>
                      <input
                        type="text"
                        value={receiptDescription}
                        onChange={(e) => setReceiptDescription(e.target.value)}
                        className="w-full bg-black/40 border border-white/20 rounded-md px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-cyan-500"
                      />
                    </div>

                    <div>
                      <label className="block text-[--color-text-secondary] mb-1">
                        Category
                      </label>
                      <select
                        value={receiptCategory}
                        onChange={(e) => setReceiptCategory(e.target.value)}
                        className="w-full bg-black/40 border border-white/20 rounded-md px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-cyan-500"
                      >
                        <option value="food">Food</option>
                        <option value="transportation">Transportation</option>
                        <option value="entertainment">Entertainment</option>
                        <option value="utilities">Utilities</option>
                        <option value="healthcare">Healthcare</option>
                        <option value="shopping">Shopping</option>
                        <option value="housing">Housing</option>
                        <option value="other">Other</option>
                        <option value="uncategorized">Uncategorized</option>
                      </select>
                    </div>

                    {receiptPreview.data.date && (
                      <div className="text-[10px] text-[--color-text-secondary] mt-1">
                        Detected date: {receiptPreview.data.date}
                      </div>
                    )}
                  </div>

                  <div className="mt-5 flex flex-col sm:flex-row gap-2">
                    <button
                      type="button"
                      onClick={handleConfirmReceipt}
                      disabled={loading}
                      className="flex-1 px-4 py-2 bg-gradient-to-r from-[--color-accent-green] to-[--color-accent-blue] rounded-md text-sm font-semibold hover:opacity-90 disabled:opacity-50"
                    >
                      {loading ? 'Saving…' : 'Create Transaction'}
                    </button>
                    <button
                      type="button"
                      onClick={handleRejectReceipt}
                      className="flex-1 px-4 py-2 bg-white/5 border border-white/10 rounded-md text-sm text-[--color-text-secondary] hover:bg-white/10"
                    >
                      Cancel
                    </button>
                  </div>
                </motion.div>
              </motion.div>
            )}
        </AnimatePresence>
    </div>
  );
}
