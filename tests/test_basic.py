from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo.fields import Date
from dateutil.relativedelta import relativedelta

class TestHospital(TransactionCase):

    def setUp(self):
        super(TestHospital, self).setUp()
        self.patient_model = self.env['hospital.patient']
        self.bed_model = self.env['hospital.bed']
        self.admission_model = self.env['hospital.admission']
        
        # Create a patient
        self.patient = self.patient_model.create({
            'name': 'Test Patient',
            'gender': 'male',
            'date_of_birth': Date.today() - relativedelta(years=25),
        })
        
        # Create a bed
        self.bed = self.bed_model.create({
            'name': 'Test Bed 1',
            'bed_type': 'standard',
            'state': 'free',
        })

    def test_patient_creation(self):
        """Test patient creation and age computation"""
        self.assertEqual(self.patient.age, 25, "Age should be 25")
        self.assertTrue(self.patient.active, "Patient should be active by default")

    def test_admission_flow(self):
        """Test admission flow: active -> bed occupied -> discharged -> bed free"""
        # Create admission
        admission = self.admission_model.create({
            'patient_id': self.patient.id,
            'bed_id': self.bed.id,
        })
        self.assertEqual(admission.state, 'draft')
        
        # Confirm admission
        admission.action_admit()
        self.assertEqual(admission.state, 'active')
        self.assertEqual(self.bed.state, 'occupied', "Bed should be occupied after admission")
        
        # Discharge
        admission.action_discharge()
        self.assertEqual(admission.state, 'discharged')
        self.assertEqual(self.bed.state, 'free', "Bed should be free after discharge")

    def test_bed_availability_constraint(self):
        """Test that we cannot admit to an occupied bed"""
        # Occupy the bed first
        self.bed.state = 'occupied'
        
        admission = self.admission_model.create({
            'patient_id': self.patient.id,
            'bed_id': self.bed.id,
        })
        
        # Try to admit - should raise ValidationError
        with self.assertRaises(ValidationError):
            admission.action_admit()
