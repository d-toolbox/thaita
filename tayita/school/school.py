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
from openerp import models, fields, api, _
import time
import openerp
import datetime
from datetime import date
from datetime import datetime
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, image_colorize, image_resize_image_big
from openerp.exceptions import except_orm, Warning, RedirectWarning
#from school import exam

class academic_year(models.Model):
    ''' Defining an academic year '''
    
    _name = "academic.year"
    _description = "Academic Year"
    _order = "sequence"
    
    sequence = fields.Integer('Sequence', required=True, help="In which sequence order you want to see this year.")
    is_current= fields.Boolean("Current Academic Year", default=False)
    name = fields.Char('Name', required=True, select=1,help='Name of  academic year')
    code = fields.Char('Code', required=True, select=1,help='Code of academic year')
    date_start = fields.Date('Start Date', required=True,help='Starting date of academic year')
    date_stop = fields.Date('End Date', required=True,help='Ending of academic year')
    semester_ids = fields.One2many('academic.semester', 'year_id', string='Semester',help="related Academic Semesters")
    grade_id = fields.Many2one('grade.master',"Grading Sequence")
    description = fields.Text('Description')

    @api.model
    def next_year(self, sequence):
        year_ids = self.search([('sequence', '>', sequence)],order='id ASC', limit=1)
        if year_ids:
            return year_ids.id
        return False
    
    @api.multi
    def name_get(self):
        res = []
        for acd_year_rec in self:
            name = "[" + acd_year_rec['code'] + "]" + acd_year_rec['name']
            res.append((acd_year_rec['id'], name))
        return res

    @api.constrains('date_start','date_stop')
    def _check_academic_year(self):
        obj_academic_ids = self.search([])
        academic_list = []
        for rec_academic in obj_academic_ids:
            academic_list.append(rec_academic.id)
        for current_academic_yr in self:
            academic_list.remove(current_academic_yr.id)
            data_academic_yr = self.browse(academic_list)
            for old_ac in data_academic_yr:
                if old_ac.date_start <= self.date_start <= old_ac.date_stop or \
                    old_ac.date_start <= self.date_stop <= old_ac.date_stop:
                    raise Warning(_('Error! You cannot define overlapping academic years.'))

    @api.constrains('date_start','date_stop')
    def _check_duration(self):
        if self.date_stop and self.date_start and self.date_stop < self.date_start:
            raise Warning(_('Error! The duration of the academic year is invalid.'))


class academic_semester(models.Model):
    ''' Defining a Semester of an academic year '''
    _name = "academic.semester"
    _description = "Academic Semester"
    _order = "date_start"
    
    name =          fields.Char('Name', required=True, help='Name of Academic Semester')
    code =          fields.Char('Code', required=True, help='Code of Academic Semester')
    date_start =    fields.Date('Start of Semester', required=True, help='Starting of Academic Semester')
    date_stop =     fields.Date('End of Semester', required=True,help='Ending of Academic Semester')
    year_id =       fields.Many2one('academic.year', 'Academic Year', required=True, help="Related Academic year ")
    description=    fields.Text('Description')

    @api.constrains('date_start','date_stop')
    def _check_duration(self):
        if self.date_stop and self.date_start and self.date_stop < self.date_start:
            raise Warning(_('Error ! The duration of the Month(s) is/are invalid.'))

    @api.constrains('year_id','date_start','date_stop')
    def _check_year_limit(self):
        if self.year_id and self.date_start and self.date_stop:
            if self.year_id.date_stop < self.date_stop or \
                self.year_id.date_stop < self.date_start or \
                self.year_id.date_start > self.date_start or \
                self.year_id.date_start > self.date_stop:
                raise Warning(_('Invalid Months ! Some months overlap or the date period is not in the scope of the academic year.'))

class subject_subject(models.Model):
    '''Defining a Module '''
    _name = "subject.subject"
    _description = "Modules"
    
    name =          fields.Char('Name', required=True)
    credit_hour=    fields.Integer("Credit Hour",required=True,help="Credit Hour for this Module")
    code =          fields.Char('Code', required=True,help="Code for this Module")
    department=     fields.Many2one('school.department',"Related Department",required=True)
    maximum_marks = fields.Integer("Maximum marks",default=100,required=True)
    minimum_marks = fields.Integer("Minimum marks",default=0,required=True)
    level =         fields.Selection([('undergraduate','Undergraduate'), 
                                          ('postgraduate','Postgraduate')
                                          ], 
                                         'Level Offered', 
                                         required=True
                                         )    
    lecturer_ids =  fields.Many2many('hr.employee','subject_lecturer_rel','subject_id','lecturer_id','Lecturer')
    year =          fields.Selection([('yr1','Year 1'), 
                                          ('yr2','Year 2'),
                                          ('yr3','Year 3'),
                                          ('yr4','Year 4')
                                          ], 
                                         'Year Lectured', 
                                         required=True
                                         )
    is_practical =  fields.Boolean('Is Practical',help='Check this if module is practical.')
    no_exam =       fields.Boolean("No Exam",help='Check this if module has no exam.')
    student_ids =   fields.Many2many('student.student','subject_id','student_id','Students')
    syllabus_ids =  fields.One2many('subject.syllabus','subject_id',string='Course Outline')

class subject_syllabus(models.Model):
    '''Defining a  Course Outline'''
    _name= "subject.syllabus"
    _description = "Course Outline"
    _rec_name = "duration"
    
    subject_id = fields.Many2one('subject.subject', 'Module')
    duration =   fields.Char("Duration")
    topic =      fields.Text("Topic")
    
class school_campus(models.Model):
    '''Campuses'''
    _name='school.campus'
    _table="school_campus"
    _description='Campus Information'
    name=fields.Char('Name')
    dvc=fields.Many2one('hr.employee','Deputy Vice Chancellor')
class school_program(models.Model):
    '''Program'''
    _name='school.program'
    _table="school_course"
    _description='Program Information'
    name=fields.Char('Name',required=True)
    department=fields.Many2one('school.department','Related Department',required=True)
    school=fields.Many2one('school.school','Related School',required=True)
    type=fields.Selection([('phd','PHD'),
                           ('masters','Masters'),
                           ('degree','Degree'),
                           ('certificate','certificate'),
                           ('od','Ordinary Diploma'),
                           ('hnd','Higher National Diploma')
                           
                           ],
                          'Type',
                          required=True)

class school_school(models.Model):
    '''Schools as used in Njala University Context'''
    _name='school.school'
    _table="school_school_njala"
    _description='Schools Information'
    name=fields.Char("Name",required=True)
    campus=fields.Many2one('school.campus',"Campus",required=True)
    dean=fields.Many2one('hr.employee','Dean of School',required=True)
    
class school_department(models.Model):
    '''Departments as used in Njala University Context'''
    _name='school.department'
    _table="school_school_department"
    _description='Departments Information'
    name=fields.Char("Name",required=True)
    campus=fields.Many2one('school.campus',"Campus",required=True)
    school=fields.Many2one('school.school',"School",required=True)
    hod=fields.Many2one('hr.employee','Head of Department',required=True)

class student_student(models.Model):
    ''' Defining a student information '''
    _name = 'student.student'
    _table = "student_student"
    _description = 'Student Information'
    _inherits = {'res.users': 'user_id'}
    
    @api.one
    def _student_name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = record.fullname + '/' + record.matt_id
        return res    
    

    @api.one
    @api.depends('date_of_birth')
    def _calc_age(self):
        self.age = 0
        fullname=str(self.student_name)+" "+str(self.middle)+" "+str(self.last)
        if self.date_of_birth:
            start = datetime.strptime(self.date_of_birth, DEFAULT_SERVER_DATE_FORMAT)
            end = datetime.strptime(time.strftime(DEFAULT_SERVER_DATE_FORMAT),DEFAULT_SERVER_DATE_FORMAT)
            self.age =  ((end - start).days / 365)
            self.fullname=fullname
    
    @api.model
    def create(self, vals):
        if vals.get('matt_id',True):
            vals['login']= vals['matt_id']
            vals['password']= vals['matt_id']
        else:
            raise except_orm(_('Error!'), _('PID not valid, so record will not save.'))
        result = super(student_student, self).create(vals)
        return result
    
    
    @api.model
    def _get_default_image(self, is_company, colorize=False):
        image = image_colorize(open(openerp.modules.get_module_resource('base', 'static/src/img', 'avatar.png')).read())
        return image_resize_image_big(image.encode('base64'))
    
    user_id =           fields.Many2one('res.users', string='User ID', ondelete="cascade", select=True, required=True)
    student_name =      fields.Char(related='user_id.name',string='Name', store=True, readonly=True)
#    pid =               fields.Char('Student ID', required=True, default=lambda obj:obj.env['ir.sequence'].get('student.student'), help='Personal IDentification Number')
    matt_id =           fields.Char('Student ID',help='Student Matriculation ID',required=True)
    contact_mobile1 =   fields.Char('Mobile no',)
    photo =             fields.Binary('Photo',default=lambda self: self._get_default_image(self._context.get('default_is_company', False)))
    year =              fields.Selection([('Year_1','Year 1'), 
                                          ('Year_2','Year 2'),
                                          ('Year_3','Year 3'),
                                          ('Year_4','Year 4')
                                          ], 
                                         'Year', 
                                         required=True
                                         )
    program =           fields.Many2one('school.program','Program')
    religion =          fields.Selection([('christianity','Christianity'), 
                                          ('islam','Islam'),
                                          ('other','Other')], 
                                         'Religion', 
                                         required=True
                                         )
    admission_date =    fields.Date('Admission Date',default=date.today())
    middle =            fields.Char('Middle Name',default="")
    last =              fields.Char('Surname', required=True)
    gender =            fields.Selection([('male','Male'), 
                                          ('female','Female')], 
                                         'Gender',
                                         required=True
                                         )
    level =             fields.Selection([('undergraduate','Undergraduate'),
                                          ('postgraduate','Postgraduate'),
                                         ],'Level',required=True, default='undergraduate')    
    date_of_birth =     fields.Date('Birthdate', required=True)
    mother_tongue =     fields.Many2one('mother.toungue',"Mother Tongue")
    age =               fields.Integer(compute='_calc_age', string='Age', readonly=True)
    maritual_status =   fields.Selection([('unmarried','Unmarried'), 
                                          ('married','Married')], 
                                         'Marital Status')
    department=         fields.Many2one('school.department','Department',required=True)
    school=             fields.Many2one('school.school','School',required=True)
    remark =            fields.Text('Remark', states={'done':[('readonly',True)]})
    state =             fields.Selection([('draft','Draft'),
                                          ('admitted','Admitted'),
                                          ('rusticated','Rusticated'),
                                          ('alumni','Alumni')],'State',readonly=True, default='draft')
    certificate_ids =   fields.One2many('student.certificate','student_id',string='Certificate')
    student_discipline_line=fields.One2many('student.descipline','student_id',string='Descipline')
    address_ids =           fields.One2many('res.partner','student_id',string='Contacts')
    citys=                  fields.Char("City")
    district =              fields.Selection([('western_rural','Western Area Rural'),
                                               ('western_urban','Western Area Urban'),
                                               ('portloko','Portloko'),
                                               ('kambia','Kambia'),
                                               ('bombali','Bombali'),
                                               ('koinadugu','Koinadugu'),
                                               ('tonkolili','Tonkolili'),
                                               ('moyamba','Moyamba'),
                                               ('bo','Bo'),
                                               ('bonthe','Bonthe'),
                                               ('kono','Kono'),
                                               ('kenema','Kenema'),
                                               ('kailahun','Kailahun'),
                                               ('pujehun','Pujehun'),
                                               ], 'District')
    hostel =                fields.Selection([('tk','Tokpombu'),
                                               ('quad','Quadrangle'),
                                               ('blocka','Matturi Block A'),
                                               ('blockb','Matturi Block B'),
                                               ('blockc','Matturi Block C'),
                                               ('blockd','Matturi Block D'),
                                               ('blocke','Matturi Block E'),
                                               ('blockf','Matturi Block F'),
                                               ('blockg','Matturi Block G'),
                                               ('blockh','Matturi Block H'),
                                               ('fc1','Florence Carew 1'),
                                               ('fc2','Florence Carew 2'),
                                               ('masters','Masters Block'),
                                               ('tourish','Tourist'),
                                               ('winters','Winters'),                   
                                               ], 'Hostel (Only Njala Campus Hostels)')  
    room_id=                fields.Char('Room Number')   
    province =              fields.Selection([('west','Western Area'),
                                               ('north','Northern Province'),
                                               ('south','Southern Province'),
                                               ('east','Eastern Province'),
                                               ], 'Province')    
    campus =                fields.Selection([('njala','Njala Campus'),
                                               ('bo','Bo Campus'),
                                               ('freetown','Freetown Campus'),
                                               ], 'Campus')      
    document =              fields.One2many('student.document','doc_id',string='Documents')
    description =           fields.One2many('student.description','des_id',string='Description')
    contact_email =         fields.Char("Email address")
    award_list =            fields.One2many('student.award','award_list_id',string='Award List')
    fullname=               fields.Char(compute='_fullname',string="Full Name")
    fullname_id=            fields.Char(compute='_student_name_get_fnc',string="Full Name n ID ",store=True)
    phone=                  fields.Char('Phone Number')
    academic_year=          fields.Many2one('academic.year', 'Academic Year')
    _sql_constraints = [('matt_unique', 'unique(matt_id)', 'Student ID must be unique!')]
    


    @api.one
    def _fullname(self):
        if self.middle:
            self.fullname=str(self.student_name)+" "+str(self.middle)+" "+str(self.last)
        else:
            self.fullname=str(self.student_name)+" "+str(self.last)
    @api.multi
    def set_to_draft(self):
        self.write({'state' : 'draft'})
        return True
    
    @api.multi
    def set_alumni(self):
        self.write({'state' : 'alumni'})
        return True
    
    @api.multi
    def set_rusticated(self):
        self.write({'state' : 'rusticated'})
        return True
    
    @api.multi
    def set_admitted(self):
        self.write({'state' : 'admitted'})
        return True
    
    @api.multi
    def admission_draft(self):
        self.write({'state' : 'draft'})
        return True

    @api.multi
    def admission_done(self):
        for student_data in self:
            if student_data.age <=15:
                raise except_orm(_('Warning'), _("The student is not eligible. Age is not valid because it's below 15 years."))
        self.write({'state': 'admitted', 'admission_date': time.strftime('%Y-%m-%d')})
        return True

class mother_tongue(models.Model):
    _name = 'mother.toungue'
    
    name = fields.Char("Mother Tongue" )

class student_award(models.Model):
    _name = 'student.award'
    
    award_list_id = fields.Many2one('student.student', 'Student')
    name =          fields.Char('Award Name',)
    description =   fields.Char('Description',)


class student_document(models.Model):
    _name = 'student.document'
    _rec_name="doc_type"
    
    doc_id =        fields.Many2one('student.student', 'Student')
    file_no =       fields.Char('File No',readonly="1",default=lambda obj:obj.env['ir.sequence'].get('student.document'))
    submited_date = fields.Date('Submitted Date')
    doc_type =      fields.Many2one('document.type', 'Document Type', required=True)
    file_name =     fields.Char('File Name',)
    return_date =   fields.Date('Return Date')
    new_datas =     fields.Binary('Attachments')

class document_type(models.Model):
    ''' Defining a Document Type(SSC,Leaving)'''
    _name = "document.type"
    _description = "Document Type"
    _rec_name="doc_type"
    _order = "seq_no"
    
    seq_no =    fields.Char('Sequence', readonly=True, default=lambda obj:obj.env['ir.sequence'].get('document.type'))
    doc_type =  fields.Char('Document Type', required=True)

class student_description(models.Model):
    ''' Defining a Student Description'''
    _name = 'student.description'
    
    des_id =        fields.Many2one('student.student', 'Description')
    name =          fields.Char('Name')
    description =   fields.Char('Description')

class student_descipline(models.Model):
    _name = 'student.descipline'
                
    student_id =    fields.Many2one('student.student', 'Student')
    teacher_id =    fields.Many2one('hr.employee', 'Teacher')
    date =          fields.Date('Date')
    year_id =       fields.Selection([('yr1','Year 1'), 
                                          ('yr2','Year 2'),
                                          ('yr3','Year 3'),
                                          ('yr4','Year 4')
                                          ], 
                                         'Year', 
                                         required=True
                                         )
    note =          fields.Text('Note')
    action_taken =  fields.Text('Action Taken')

class student_certificate(models.Model):
    _name = "student.certificate"
                
    student_id =    fields.Many2one('student.student', 'Student')
    description =   fields.Char('Description')
    certi =         fields.Binary('Certificate',required =True)

class hr_employee(models.Model):
    ''' Defining a Lecturer information '''
    _name = 'hr.employee'
    _inherit = 'hr.employee'
    _description = 'Lecturer Information'
    
    @api.one
    def _compute_subject(self):
        ''' This function will automatically computes the modules related to particular lecturer.'''
        subject_obj = self.env['subject.subject']
        subject_ids = subject_obj.search([('teacher_ids.id','=',self.id)])
        sub_list = []
        for sub_rec in subject_ids:
            sub_list.append(sub_rec.id)
        self.subject_ids = sub_list
    subject_ids = fields.Many2many('subject.subject','hr_employee_rel', compute='_compute_subject', string='Modules')

class res_partner(models.Model):
    '''Defining a address information '''
    _inherit = 'res.partner'
    _description = 'Address Information'
    
    student_id = fields.Many2one('student.student','Student')

class student_reference(models.Model):
    ''' Defining a student reference information '''
    _name = "student.reference"
    _description = "Student Reference"
    
    reference_id =  fields.Many2one('student.student', 'Student')
    name =          fields.Char('First Name', required=True)
    middle =        fields.Char('Middle Name', required=True)
    last =          fields.Char('Surname', required=True)
    designation =   fields.Char('Designation', required=True)
    phone =         fields.Char('Phone', required=True)
    gender =        fields.Selection([('male','Male'), ('female','Female')], 'Gender')

class student_family_contact(models.Model):
    ''' Defining a student emergency contact information '''
    _name = "student.family.contact"
    _description = "Student Family Contact"
    
    family_contact_id = fields.Many2one('student.student', string='Student')
    rel_name =          fields.Selection([('exist','Link to Existing Student'), ('new','Create New Relative Name')], 'Related Student', help="Select Name", required=True)
    user_id =           fields.Many2one('res.users', string='User ID', ondelete="cascade", select=True, required=True)
    stu_name =          fields.Char(related='user_id.name',string='Name',help="Select Student From Existing List")
    name =              fields.Char('Name')
    relation =          fields.Many2one('student.relation.master',string='Relation', required=True)
    phone =             fields.Char('Phone', required=True)
    email =             fields.Char('E-Mail')

class student_relation_master(models.Model):
    ''' Student Relation Information '''
    _name = "student.relation.master"
    _description = "Student Relation Master"
    name =   fields.Char('Name',required=True,help="Enter Relation name")
    seq_no = fields.Integer('Sequence')

class grade_master(models.Model):
    _name = 'grade.master'
    
    name =      fields.Char('Grading Sequence', select=1, required=True)
    grade_ids = fields.One2many('grade.line','grade_id', string='Grading Sequence')

class grade_line(models.Model):
    _name = 'grade.line'
    
    from_mark =         fields.Integer("From Marks",required=True, help="The grade will starts from this marks.")
    interpretation=     fields.Integer("Interpretation",required=True,help="Interpretation of grade as used in Njala context eg. A=5,B=4,C=3 etc")
    to_mark =           fields.Integer('To Marks',required=True, help="The grade will ends to this marks.")
    grade =             fields.Char('Grading Sequence', required=True, help="Grading sequence")
    sequence =          fields.Integer('Sequence',help="Sequence order of the grade.")
    fail =              fields.Boolean("Fail",help="If fail field is set to True, it will allow you to set the grade as fail.")
    grade_id =          fields.Many2one("grade.master",'Grade')
    name =              fields.Char('Name')

class student_news(models.Model):
    _name='student.news'
    _description = 'Student News'
    _rec_name = 'subject'
    
    subject =       fields.Char('Subject', required=True, help="Subject of the news.") 
    description =   fields.Text('Description',help="Description")
    date =          fields.Datetime('Expiry Date',help="Expiry date of the news.")
    user_ids =      fields.Many2many('res.users','user_news_rel','id','user_ids','User News',help="Name to whom this news is related.")
    color =         fields.Integer('Color Index', default=0)
    
    
    @api.multi
    def news_update(self):
        emp_obj = self.env['hr.employee']
        obj_mail_server = self.env['ir.mail_server']
        mail_server_ids = obj_mail_server.search([])
        if not mail_server_ids:
            raise except_orm(_('Mail Error'), _('No mail outgoing mail server specified!'))
        mail_server_record = mail_server_ids[0]
        email_list = []
        for news in self:
            if news.user_ids:
                for user in news.user_ids:
                    if user.email:
                        email_list.append(user.email)
                if not email_list:
                    raise except_orm(_('User Email Configuration '), _("Email not found in users !"))
            else:
                for employee in emp_obj.search([]):
                    if employee.work_email:
                        email_list.append(employee.work_email)
                    elif employee.user_id and employee.user_id.email:
                        email_list.append(employee.user_id.email)
                if not email_list:
                    raise except_orm(_('Mail Error' ), _("Email not defined!")) 
#            rec_date = fields.datetime.context_timestamp(datetime.strptime(news.date, DEFAULT_SERVER_DATETIME_FORMAT))
            t= datetime.strptime(news.date, '%Y-%m-%d %H:%M:%S')
            body =  'Hi,<br/><br/> \
                This is a news update from <b>%s</b> posted at %s<br/><br/>\
                %s <br/><br/>\
                Thank you.' % (self._cr.dbname, t.strftime('%d-%m-%Y %H:%M:%S'), news.description )
            message  = obj_mail_server.build_email(
                            email_from=mail_server_record.smtp_user, 
                            email_to=email_list, 
                            subject='Notification for news update.', 
                            body=body, 
                            body_alternative=body, 
                            email_cc=None, 
                            email_bcc=None, 
                            reply_to=mail_server_record.smtp_user, 
                            attachments=None, 
                            references = None, 
                            object_id=None, 
                            subtype='html', #It can be plain or html
                            subtype_alternative=None, 
                            headers=None)
            obj_mail_server.send_email(message=message, mail_server_id=mail_server_ids[0].id)
        return True


class student_reminder(models.Model):
    _name = 'student.reminder'
    
    stu_id =        fields.Many2one('student.student',' Student Name',required = True)
    name =          fields.Char('Title')
    date =          fields.Date('Date')
    description =   fields.Text('Description')
    color =         fields.Integer('Color Index', default=0)


class res_users(models.Model):
    _inherit = 'res.users'
    
    @api.model
    def create(self,vals):
        vals.update({'employee_ids':False})
        res = super(res_users, self).create(vals)
        return res
        
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: