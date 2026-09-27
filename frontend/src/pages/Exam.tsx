import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

interface Question {
  id: str;
  text: str;
  question_type: str;
  difficulty: str;
  marks: number;
  options?: { id: str, text: str }[];
}

interface ExamSession {
  session_id: str;
  assessment_id: str;
  status: str;
  start_time: str;
  end_time: str;
  questions: Question[];
}

export default function Exam() {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const navigate = useNavigate();
  const [session, setSession] = useState<ExamSession | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [currentQIndex, setCurrentQIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [timeLeft, setTimeLeft] = useState<number | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [examSubmitted, setExamSubmitted] = useState(false);

  const studentId = "student_demo_1"; // Mock student ID for now

  const startExam = async () => {
    if (!assessmentId) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`http://localhost:8000/api/v1/exams/${assessmentId}/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Student-ID': studentId
        }
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to start exam');
      }
      const data = await res.json();
      setSession(data);
      calculateTimeLeft(data.end_time);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const calculateTimeLeft = (endTimeStr: string) => {
    const end = new Date(endTimeStr).getTime();
    const now = new Date().getTime();
    setTimeLeft(Math.max(0, Math.floor((end - now) / 1000)));
  };

  useEffect(() => {
    if (session && timeLeft !== null && timeLeft > 0 && !examSubmitted) {
      const timerId = setInterval(() => {
        setTimeLeft(prev => {
          if (prev && prev <= 1) {
            clearInterval(timerId);
            submitExam(true);
            return 0;
          }
          return prev ? prev - 1 : 0;
        });
      }, 1000);
      return () => clearInterval(timerId);
    }
  }, [session, timeLeft, examSubmitted]);

  // Autosave when answer changes (debounced/periodic in real app, immediate here for simplicity)
  const saveAnswer = async (questionId: string, answer: any) => {
    if (!session || examSubmitted) return;
    try {
      await fetch(`http://localhost:8000/api/v1/exams/${session.session_id}/answers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Student-ID': studentId
        },
        body: JSON.stringify([{ question_id: questionId, student_answer: answer }])
      });
    } catch (e) {
      console.error("Autosave failed", e);
    }
  };

  const handleAnswerChange = (questionId: string, answer: any) => {
    setAnswers(prev => ({ ...prev, [questionId]: answer }));
    saveAnswer(questionId, answer);
  };

  const submitExam = async (auto = false) => {
    if (!session || isSubmitting) return;
    setIsSubmitting(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/exams/${session.session_id}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Student-ID': studentId
        }
      });
      if (!res.ok) throw new Error('Failed to submit exam');
      setExamSubmitted(true);
    } catch (err: any) {
      if (!auto) setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (examSubmitted) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="bg-white p-8 rounded-3xl shadow-lg text-center max-w-md w-full border border-gray-100">
          <div className="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Exam Submitted Successfully</h2>
          <p className="text-gray-500 mb-8">Your responses have been recorded. You can now close this page or return to the dashboard.</p>
          <button 
            onClick={() => navigate('/')}
            className="w-full py-3 bg-gray-900 text-white rounded-xl font-medium hover:bg-gray-800 transition-colors"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] max-w-2xl mx-auto">
        <div className="bg-white p-10 rounded-3xl shadow-sm border border-gray-100 w-full">
          <h1 className="text-3xl font-bold text-gray-800 mb-4">Start Assessment</h1>
          <p className="text-gray-600 mb-8 text-lg">
            You are about to start assessment <span className="font-semibold">{assessmentId}</span>. 
            Ensure you have a stable internet connection. The timer will begin immediately.
          </p>
          
          <div className="bg-blue-50/50 rounded-2xl p-6 mb-8 border border-blue-100/50">
            <h3 className="font-semibold text-blue-900 mb-2">Instructions</h3>
            <ul className="list-disc list-inside text-blue-800/80 space-y-2">
              <li>Do not refresh the page during the exam.</li>
              <li>Your answers are autosaved automatically.</li>
              <li>The exam will auto-submit when the time expires.</li>
            </ul>
          </div>

          {error && <div className="mb-6 p-4 bg-red-50 text-red-600 rounded-xl">{error}</div>}
          
          <button 
            onClick={startExam}
            disabled={loading}
            className="w-full py-4 bg-indigo-600 text-white rounded-2xl font-semibold text-lg hover:bg-indigo-700 transition-all shadow-md shadow-indigo-200 disabled:opacity-50"
          >
            {loading ? 'Starting...' : 'Start Exam Now'}
          </button>
        </div>
      </div>
    );
  }

  const formatTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const question = session.questions[currentQIndex];

  return (
    <div className="max-w-5xl mx-auto flex flex-col md:flex-row gap-6 pb-20">
      
      {/* Sidebar Navigation */}
      <div className="w-full md:w-64 shrink-0">
        <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 sticky top-6">
          <div className="text-center mb-6">
            <div className="text-sm font-medium text-gray-400 mb-1">Time Remaining</div>
            <div className={`text-3xl font-bold font-mono tracking-tight ${timeLeft !== null && timeLeft < 300 ? 'text-red-500' : 'text-gray-800'}`}>
              {timeLeft !== null ? formatTime(timeLeft) : '--:--'}
            </div>
          </div>
          
          <div className="grid grid-cols-5 gap-2 mb-8">
            {session.questions.map((q, idx) => (
              <button
                key={q.id}
                onClick={() => setCurrentQIndex(idx)}
                className={`
                  w-10 h-10 rounded-xl font-medium text-sm flex items-center justify-center transition-colors
                  ${idx === currentQIndex ? 'ring-2 ring-indigo-500 ring-offset-2' : ''}
                  ${answers[q.id] !== undefined 
                    ? 'bg-indigo-100 text-indigo-700' 
                    : 'bg-gray-50 text-gray-500 hover:bg-gray-100'}
                `}
              >
                {idx + 1}
              </button>
            ))}
          </div>

          <button 
            onClick={() => submitExam()}
            disabled={isSubmitting}
            className="w-full py-3 bg-red-50 text-red-600 font-semibold rounded-xl hover:bg-red-100 transition-colors border border-red-100"
          >
            {isSubmitting ? 'Submitting...' : 'Finish Exam'}
          </button>
        </div>
      </div>

      {/* Main Question Area */}
      <div className="flex-1 min-w-0">
        <div className="bg-white rounded-3xl p-8 md:p-10 shadow-sm border border-gray-100">
          <div className="flex justify-between items-center mb-6 pb-6 border-b border-gray-100">
            <h2 className="text-xl font-semibold text-gray-800">Question {currentQIndex + 1} of {session.questions.length}</h2>
            <div className="px-3 py-1 bg-gray-100 text-gray-600 text-sm font-medium rounded-full">
              {question.marks} {question.marks === 1 ? 'Mark' : 'Marks'}
            </div>
          </div>
          
          <div className="prose max-w-none mb-10">
            <p className="text-lg text-gray-800 leading-relaxed">{question.text}</p>
          </div>

          <div className="space-y-4">
            {question.question_type === 'mcq' && question.options && (
              <div className="grid grid-cols-1 gap-3">
                {question.options.map((opt) => (
                  <label 
                    key={opt.id} 
                    className={`
                      flex items-center p-4 rounded-2xl border-2 cursor-pointer transition-all
                      ${answers[question.id] === opt.id 
                        ? 'border-indigo-500 bg-indigo-50' 
                        : 'border-gray-100 hover:border-gray-200 hover:bg-gray-50'}
                    `}
                  >
                    <input 
                      type="radio" 
                      name={`q-${question.id}`} 
                      value={opt.id}
                      checked={answers[question.id] === opt.id}
                      onChange={() => handleAnswerChange(question.id, opt.id)}
                      className="w-5 h-5 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span className="ml-3 text-gray-700 text-lg">{opt.text}</span>
                  </label>
                ))}
              </div>
            )}
            
            {(question.question_type === 'short_answer' || question.question_type === 'fill_in_blank') && (
              <input 
                type="text" 
                value={answers[question.id] || ''}
                onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                placeholder="Type your answer here..."
                className="w-full p-4 rounded-2xl border-2 border-gray-100 focus:border-indigo-500 focus:ring-0 text-lg transition-colors"
              />
            )}

            {question.question_type === 'descriptive' && (
              <textarea 
                rows={8}
                value={answers[question.id] || ''}
                onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                placeholder="Write your detailed answer here..."
                className="w-full p-4 rounded-2xl border-2 border-gray-100 focus:border-indigo-500 focus:ring-0 text-lg transition-colors resize-none"
              ></textarea>
            )}
          </div>
        </div>

        <div className="flex justify-between items-center mt-6">
          <button 
            onClick={() => setCurrentQIndex(prev => Math.max(0, prev - 1))}
            disabled={currentQIndex === 0}
            className="px-6 py-3 bg-white border border-gray-200 text-gray-700 font-medium rounded-xl hover:bg-gray-50 disabled:opacity-50 transition-colors"
          >
            Previous
          </button>
          
          <button 
            onClick={() => setCurrentQIndex(prev => Math.min(session.questions.length - 1, prev + 1))}
            disabled={currentQIndex === session.questions.length - 1}
            className="px-6 py-3 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 disabled:opacity-50 shadow-sm shadow-indigo-200 transition-colors"
          >
            Next Question
          </button>
        </div>
      </div>
    </div>
  );
}
