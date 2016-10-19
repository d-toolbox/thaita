# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2011-2012 Serpent Consulting Services (<http://www.serpentcs.com>)
#    Copyright (C) 2013-2014 Serpent Consulting Services (<http://www.serpentcs.com>)
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import date, datetime
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning

class extended_time_table(models.Model):
    
    _inherit = 'time.table'
    
    timetable_type = fields.Selection([('exam', 'Exam'), ('regular', 'Regular')], "Time Table Type", required=True)
    exam_id = fields.Many2one('exam.exam', 'Exam')
    
class extended_student_student(models.Model):
      
    _inherit = 'student.student'
    
    exam_results_ids = fields.One2many('exam.result','student_id','Exam History',readonly=True)
    
class extended_time_table_line(models.Model):
    
    _inherit = 'time.table.line'
    
    exm_date = fields.Date('Exam Date')
    day_of_week = fields.Char('Week Day')
    
    @api.multi
    def on_change_date_day(self,exm_date):
        val = {}
        if exm_date:
            val['week_day'] = datetime.strptime(exm_date, "%Y-%m-%d").strftime("%A").lower()
        return {'value' : val}
    
    @api.multi
    def _check_date(self):
        for line in self:
            if line.exm_date:
                dt = datetime.strptime(line.exm_date, "%Y-%m-%d")
                if line.week_day != datetime.strptime(line.exm_date, "%Y-%m-%d").strftime("%A").lower():
                    return False
                elif dt.__str__() < datetime.strptime(date.today().__str__(), "%Y-%m-%d").__str__():
                    raise except_orm(_('Invalid Date Error !'), _('Either you have selected wrong day for the date or you have selected invalid date.'))
        return True
    
class exam_exam(models.Model):
   
    _name = 'exam.exam'
    _description = 'Exam Information'
    
    name = fields.Char("Exam Name", required = True)
    exam_code = fields.Char('Exam Code', required=True, readonly=True,default=lambda obj:obj.env['ir.sequence'].get('exam.exam'))
    start_date = fields.Date("Exam Start Date",help="Exam will start from this date")
    end_date = fields.Date("Exam End date", help="Exam will end at this date")
    create_date = fields.Date("Exam Created Date", help="Exam Created Date")
    write_date = fields.Date("Exam Update Date", help="Exam Update Date")
    exam_timetable_ids = fields.One2many('time.table', 'exam_id', 'Exam Schedule')
    state = fields.Selection([('draft','Draft'),('running','Running'),('finished','Finished'),('cancelled','Cancelled')], 'State', readonly=True,default='draft')
    
    @api.multi
    def set_to_draft(self):
        self.write({'state' : 'draft'})
    
    @api.multi
    def set_running(self):
        if self.exam_timetable_ids:
            self.write({'state' : 'running'})
        else:
            raise except_orm(_('Exam Schedule'), _('You must add one Exam Schedule'))
    
    @api.multi
    def set_finish(self):
        self.write({'state' : 'finished'})
    
    @api.multi
    def set_cancel(self):
        self.write({'state' : 'cancelled'})
        
    @api.multi
    def _validate_date(self):
        for exm in self:
            if exm.start_date > exm.end_date:
                return False
        return True

class additional_exam(models.Model):
    
    _name = 'additional.exam'
    _description = 'additional Exam Information'
    
    name = fields.Char("Additional Exam Name",required=True)
    addtional_exam_code = fields.Char('Exam Code', required=True, readonly=True,default=lambda obj:obj.env['ir.sequence'].get('additional.exam'))
    subject_id = fields.Many2one("subject.subject", "Subject Name")
    exam_date = fields.Date("Exam Date")
    maximum_marks = fields.Integer("Maximum Mark")
    minimum_marks = fields.Integer("Minimum Mark")
    create_date = fields.Date("Created Date", help="Exam Created Date")
    write_date = fields.Date("Updated date", help="Exam Updated Date")
    

class exam_result(models.Model):
    
    _name = 'exam.result'
    _rec_name = 's_exam_ids'
    _description = 'exam result Information'

    @api.one
    @api.depends('result_ids')
    def _compute_total(self):
        total=0.0
        if self.result_ids:
            for line in self.result_ids:
                obtain_marks = line.obtain_marks
                if line.state == "re-evaluation":
                    obtain_marks = line.marks_reeval
                elif line.state == "re-access":
                    obtain_marks = line.marks_access
                total += obtain_marks
            self.total = total
            
            
            
    @api.one
    @api.depends('result_ids')
    def _compute_sgpa(self):
        totalgr=0.0
        totalcr=0.0
        amount=0
        if self.result_ids:
            for line in self.result_ids:
                amount+=1
                interpretation = line.interpretation
                credit_hour=line.credit_hour
                mul=interpretation*credit_hour
                totalgr += mul
                totalcr+=credit_hour
        if amount>0:        
            total=totalgr/totalcr
        else:
            total=0.0
        self.totalgp = total
            #credit_hour, value
                       
    @api.one
    @api.depends('result_ids')
    def _compute_gpa(self):
        total=0.0
        if self.result_ids:
            for line in self.result_ids:
                obtain_marks = line.obtain_marks
                if line.state == "re-evaluation":
                    obtain_marks = line.marks_reeval
                elif line.state == "re-access":
                    obtain_marks = line.marks_access
                total += obtain_marks
            self.total = total
                    
            
            
            
    @api.multi 
    def _compute_per(self):
        res={}
        for result in self.browse(self.ids):
            total = 0.0
            obtained_total = 0.0
            obtain_marks = 0.0
            per = 0.0
            grd = ""
            for sub_line in result.result_ids:
                if sub_line.state == "re-evaluation":
                    obtain_marks = sub_line.marks_reeval
                elif sub_line.state == "re-access":
                    obtain_marks = sub_line.marks_access
                obtain_marks = sub_line.obtain_marks
                total += sub_line.maximum_marks or 0
                obtained_total += obtain_marks
            if total != 0.0:
                per = (obtained_total/total)  * 100
                for grade_id in result.student_id.academic_year.grade_id.grade_ids:
                    if per >= grade_id.from_mark and per <= grade_id.to_mark: 
                        grd = grade_id.grade
                res[result.id] = {'percentage':per,'grade':grd}
        return res

    @api.one
    @api.depends('result_ids','student_id')
    def _compute_result(self):
        flag = False
        if self.result_ids and self.student_id:
            if self.student_id.academic_year.grade_id.grade_ids:
                    if self.totalgp>2.99:
                        self.result = 'Pass'
                    else:
                        flag=True
            else:
                raise except_orm(_('Configuration Error !'), _('First Select Grade System in Student->year->.'))
        if flag:
            self.result = 'Fail'
    

    s_exam_ids = fields.Many2one("exam.exam", "Examination",required = True)
    student_id = fields.Many2one("student.student", "Student Name", required = True)
    semester=   fields.Selection([('first_semester',"First Semester"),
                                  ('second_semester',"Second Semester"),
                                  ],
                                "Semester",
                                required=True)
    matt_id = fields.Char(related='student_id.matt_id', string="Student ID", readonly=True)
    result_ids = fields.One2many("exam.subject","exam_id","Exam Subjects")
    total = fields.Float(compute='_compute_total', string ='Obtain Total', method=True,store=True)
    totalgp = fields.Float(compute='_compute_sgpa', string ='Grade Point Average', method=True,store=True)
    re_total = fields.Float('Re-access Obtain Total', readonly=True)
    percentage = fields.Float("Percentage", readonly=True )
    result = fields.Char(compute='_compute_result', string ='Result', readonly=True, method=True, store=True)
    grade = fields.Char("Grade", readonly=True)
    state = fields.Selection([('draft','Draft'), ('confirm','Awaiting Confirmation'), ('hod-approve','Awaiting HOD Approval'),('dean-approve','Awaiting Dean Approval'), ('registry-approve','Awaiting Registry Approval'),('done','Done')], 'State', readonly=True,default='draft')
    color = fields.Integer('Color')
    student_year = fields.Char(compute='_year', string="Year", readonly=True)
    student_name=  fields.Char(compute='_fullname',string="Student Name")
    
    student_program=  fields.Char(related='student_id.program.name', string="Program", readonly=True)
    student_academic_year=  fields.Char(related='student_id.academic_year.code', string="Academic Year", readonly=True)
    
    
    @api.one
    def _year(self):
        if self.student_id:
            self.student_year=self.student_id.year   
    @api.one
    def _program(self):
        if self.student_id:
            self.student_year=self.student_id.program.name  
    @api.one
    def _academic_year(self):
        if self.student_id:
            self.student_year=self.student_id.academic_year.code        
    
    @api.one
    def _fullname(self):
        if self.student_id:
            self.student_name=self.student_id.fullname
    
    @api.multi
    def result_validate(self):
        self.write({'state':'confirm'})
    
    @api.multi
    def result_confirm(self):
        self.write({'state':'hod-approve'})
        
    @api.multi
    def hod_approve(self):
        self.write({'state':'dean-approve'})
        
    @api.multi
    def dean_approve(self):
        self.write({'state':'registry-approve'})   
    @api.multi
    def registry_approve(self):
        self.write({'state':'done'})         
  

class exam_grade_line(models.Model):
    _name = "exam.grade.line"
    _description = 'Exam Subject Information'
    
    exam_id = fields.Many2one('exam.result', 'Result')
    grade = fields.Char(string='Grade')

class exam_subject(models.Model):
    _name = "exam.subject"
    _description = 'Exam Subject Information'
    _rec_name = 'subject_id'
    
    @api.constrains('obtain_marks','minimum_marks')
    def _validate_marks(self):
        if self.obtain_marks > self.maximum_marks or self.minimum_marks > self.maximum_marks:
            raise Warning(_('The obtained marks and minimum marks should not extend maximum marks.'))
    

    @api.one
    @api.depends('exam_id','obtain_marks')
    def _get_grade(self):
        if self.exam_id and self.exam_id.student_id and self.exam_id.student_id.academic_year.grade_id.grade_ids:
            for grade_id in self.exam_id.student_id.academic_year.grade_id.grade_ids:
                if self.obtain_marks >= grade_id.from_mark and self.obtain_marks <= grade_id.to_mark:
                    self.grade = grade_id.grade
                    
    @api.one
    @api.depends('exam_id','obtain_marks')
    def _get_value(self):
        if self.exam_id and self.exam_id.student_id and self.exam_id.student_id.academic_year.grade_id.grade_ids:
            for grade_id in self.exam_id.student_id.academic_year.grade_id.grade_ids:
                if self.obtain_marks >= grade_id.from_mark and self.obtain_marks <= grade_id.to_mark:
                    self.interpretation = grade_id.interpretation                    
                    
    exam_id = fields.Many2one('exam.result', 'Result')
    state = fields.Selection([('draft','Draft'), ('confirm','Confirm'), ('re-access','Re-Access'),('re-access_confirm','Re-Access-Confirm'), ('re-evaluation','Re-Evaluation'),('re-evaluation_confirm','Re-Evaluation Confirm')], related='exam_id.state',string="State")
    subject_id = fields.Many2one("subject.subject","Module Name")
    obtain_marks = fields.Float("Mark Obtained", group_operator="avg")
    #credit_hour=    fields.Integer("Credit Hour")
    credit_hour=    fields.Integer(related='subject_id.credit_hour',string="Credit Hour")
    minimum_marks = fields.Float("Minimum Marks")
    maximum_marks = fields.Float("Maximum Marks",default=100.0)
    marks_access = fields.Float("Marks After Access")
    marks_reeval = fields.Float("Marks After Re-evaluation")
    grade_id = fields.Many2one('grade.master',"Grade")
#    grade=    fields.Integer(related='grade_id.grade_ids.grade',string="Grade")
#    value=    fields.Integer(related='grade_id.grade_ids.interpretation',string="Interpretation")
    
    grade = fields.Char(compute='_get_grade', string='Grade', type="char")
    interpretation=fields.Integer(compute='_get_value', string='Interpretation')

    
class additional_exam_result(models.Model):

    _name = 'additional.exam.result'
    _description = 'subject result Information'
    
    @api.one
    @api.depends('a_exam_id','obtain_marks')
    def _calc_result(self):
        if self.a_exam_id and self.a_exam_id.subject_id and self.a_exam_id.subject_id.minimum_marks:
            if self.a_exam_id.subject_id.minimum_marks <= self.obtain_marks:
                self.result = 'Pass'
            else:
                self.result = 'Fail'
    
    
    @api.constrains('obtain_marks')
    def _validate_marks(self):
        if self.obtain_marks > self.a_exam_id.subject_id.maximum_marks:
            raise Warning(_('The obtained marks should not extend maximum marks.'))
        return True

    a_exam_id = fields.Many2one("additional.exam", "Additional Examination", required=True)
    student_id = fields.Many2one("student.student", "Student Name", required=True)
    obtain_marks = fields.Float("Mark Obtained")
    result = fields.Char(compute='_calc_result',string ='Result', method=True)
    student_name=  fields.Char(compute='_fullname',string="Student Name")
    
    
    @api.one
    def _fullname(self):
        if self.student_id:
            self.student_name=self.student_id.fullname

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
