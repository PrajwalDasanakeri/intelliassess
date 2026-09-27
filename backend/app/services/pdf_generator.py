import os
from fpdf import FPDF
from app.schemas.question_paper import QuestionPaperInDB
from app.schemas.assessment import AssessmentInDB
from app.schemas.enums import QuestionType

class PDFGenerator:
    def generate_question_paper_pdf(self, paper: QuestionPaperInDB, assessment: AssessmentInDB, output_path: str):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Heading
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "IntelliAssess Question Paper", ln=True, align="C")
        
        # Meta info
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 8, f"Assessment: {assessment.title} (Version {paper.version})", ln=True, align="C")
        pdf.cell(0, 8, f"Subject: {assessment.subject} | Class: {assessment.class_level}", ln=True, align="C")
        pdf.cell(0, 8, f"Duration: {assessment.duration_minutes} mins | Max Marks: {paper.total_marks}", ln=True, align="C")
        
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Instructions:", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, "1. Read all questions carefully.\n2. Attempt all questions.\n3. The marks for each question are indicated on the right.")
        pdf.ln(10)
        
        # Questions
        for idx, q in enumerate(paper.questions, start=1):
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(10, 8, f"Q{idx}.", align="L")
            
            # Marks aligned right
            pdf.set_xy(pdf.w - 30, pdf.get_y())
            pdf.cell(20, 8, f"[{q.marks} Marks]", align="R", ln=True)
            
            # Question Text
            pdf.set_xy(10, pdf.get_y())
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 6, q.text)
            
            if q.question_type == QuestionType.MCQ and q.options:
                pdf.ln(2)
                for opt in q.options:
                    pdf.set_x(20)
                    pdf.cell(0, 6, f"{opt.id}) {opt.text}", ln=True)
            
            pdf.ln(6)
            
        pdf.output(output_path)
