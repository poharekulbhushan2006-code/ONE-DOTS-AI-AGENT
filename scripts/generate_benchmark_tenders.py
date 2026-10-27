"""
Benchmark Tender Document Generator for AXIS Tender Intelligence
Generates 15 authentic, multi-page government tender PDFs across Maharashtra PWD, CPWD, and NHAI
calibrating edge cases:
- Currency notations (Cr, Lakhs, INR)
- Complex multi-tiered eligibility clauses (Turnover, Solvency, Similar Works 80%/50%/40%)
- Statutory checklists (GST, PAN, EPF, Non-Blacklisted Affidavits)
- Plant & machinery requirements
- Defect Liability Periods (12 to 60 months)
"""

import os
import json
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Adds running headers and footers with page numbering."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (Pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "GOVERNMENT E-PROCUREMENT TENDER DOCUMENT — NOTICE INVITING TENDER")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Footer
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)
        self.drawString(54, 32, "CONFIDENTIAL & PROPRIETARY — STRICTLY FOR ELIGIBLE ENLISTED BIDDERS")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_str)
        self.restoreState()


BENCHMARK_SPECIFICATIONS = [
    # 1. Maharashtra PWD
    {
        "id": "PWD-MH-2026-HW-402",
        "filename": "benchmark_01_mahapwd_highway_sh42.pdf",
        "authority": "PUBLIC WORKS DEPARTMENT, GOVERNMENT OF MAHARASHTRA",
        "division": "OFFICE OF THE SUPERINTENDING ENGINEER, PWD CIRCLE PUNE",
        "work_name": "Widening and Strengthening of 2-Lane State Highway-42 from Km 12/000 to 34/500 in District Pune",
        "nit_no": "e-Tender Notice No. NIT-2026/PWD/PUNE/HIGHWAY-402",
        "tender_id": "2026_PWD_88412_1",
        "estimated_cost_str": "Rs. 18,50,00,000/- (Rupees Eighteen Crores Fifty Lakhs only)",
        "estimated_cost_val": 185000000.0,
        "emd_str": "Rs. 37,00,000/- (Rupees Thirty-Seven Lakhs only, 2% of Estimated Cost)",
        "tender_fee_str": "Rs. 10,000/- plus 18% GST (Non-refundable)",
        "turnover_clause": "Average annual financial turnover during last 3 consecutive financial years (FY 2022-23, FY 2023-24, and FY 2024-25) shall not be less than 50% of the estimated cost (Rs. 9.25 Crores).",
        "solvency_clause": "Contractor must submit a Bank Solvency Certificate of minimum 40% of estimated cost (Rs. 7.40 Crores) from any Nationalized or Scheduled Commercial Bank.",
        "similar_work_clause": "Experience of completed similar road work: One work of value not less than 80% of estimated cost (Rs. 14.80 Cr), OR Two works each of not less than 50% (Rs. 9.25 Cr), OR Three works each of not less than 40% (Rs. 7.40 Cr).",
        "contractor_class": "Class I (Civil) enlisted with Maharashtra PWD or CPWD",
        "completion_period": "18 Months (including monsoon season)",
        "dlp": "36 Months from the date of physical completion",
        "bid_validity": "120 Days from technical bid opening date",
        "machinery": ["1 Hot Mix Plant (100-120 TPH)", "1 Sensor Paver with electronic sensing", "2 Vibratory Tandem Rollers", "1 Pneumatic Tyre Roller"]
    },
    {
        "id": "PWD-MH-2026-BR-118",
        "filename": "benchmark_02_mahapwd_bridge_godavari.pdf",
        "authority": "PUBLIC WORKS DEPARTMENT, GOVERNMENT OF MAHARASHTRA",
        "division": "EXECUTIVE ENGINEER, PWD BRIDGES DIVISION NASHIK",
        "work_name": "Construction of High Level Major PSC Girder Bridge over Godavari River with Approaches on Niphad-Yeola Road",
        "nit_no": "NIT No. PWD/NSK/BRG/2026/118",
        "tender_id": "2026_PWD_91044_2",
        "estimated_cost_str": "Rs. 42,80,00,000/- (Rupees Forty-Two Crores Eighty Lakhs only)",
        "estimated_cost_val": 428000000.0,
        "emd_str": "Rs. 42,80,000/- (1% of Estimated Cost through Online Payment Gateway)",
        "tender_fee_str": "Rs. 15,000/-",
        "turnover_clause": "The average annual turnover of the bidder during the last 3 financial years must exceed 60% of estimated cost (Rs. 25.68 Crores).",
        "solvency_clause": "Solvency certificate of at least Rs. 17.12 Crores (40% of estimated cost) issued by a scheduled bank within 6 months.",
        "similar_work_clause": "Successful completion of at least one major bridge project over river having well sinking foundation of value Rs. 34.24 Cr (80%), or two works of Rs. 21.40 Cr (50%).",
        "contractor_class": "Class I-A (Bridges & Heavy Infrastructure) PWD Maharashtra",
        "completion_period": "24 Months",
        "dlp": "60 Months (5 Years Comprehensive Warranty)",
        "bid_validity": "180 Days",
        "machinery": ["2 Hydraulic Rotary Piling Rigs", "1 Concrete Batching Plant (60 m3/hr)", "4 Transit Mixers", "1 Mobile Crane 50T"]
    },
    {
        "id": "PWD-MH-2026-BLDG-55",
        "filename": "benchmark_03_mahapwd_collectorate_pune.pdf",
        "authority": "PUBLIC WORKS DEPARTMENT, MAHARASHTRA",
        "division": "EXECUTIVE ENGINEER, PWD SPECIAL BUILDINGS DIVISION PUNE",
        "work_name": "Construction of Integrated District Administrative Complex (New Collectorate Building G+7) at Haveli, Pune",
        "nit_no": "e-Tender Notice No. PWD/PUNE/SBD/2026/055",
        "tender_id": "2026_PWD_73421_3",
        "estimated_cost_str": "Rs. 28,40,00,000/- (Rupees Twenty-Eight Crores Forty Lakhs only)",
        "estimated_cost_val": 284000000.0,
        "emd_str": "Rs. 28,40,000/- (1% EMD via online payment)",
        "tender_fee_str": "Rs. 12,000/-",
        "turnover_clause": "Average annual turnover of Rs. 14.20 Crores (50% of cost) over the preceding 3 financial years.",
        "solvency_clause": "Bank solvency of minimum Rs. 11.36 Crores (40%) issued by a nationalized or scheduled bank.",
        "similar_work_clause": "Experience of constructing multi-storey RCC institutional/office buildings of value not less than Rs. 22.72 Cr (80%) or two works of Rs. 14.20 Cr (50%).",
        "contractor_class": "Class I (Civil Buildings) PWD or CPWD",
        "completion_period": "18 Months",
        "dlp": "36 Months",
        "bid_validity": "90 Days",
        "machinery": ["1 Tower Crane (40m jib)", "2 Concrete Pumps", "1 Batching Plant (30 m3/hr)", "Scaffolding & Formwork System 10,000 sqm"]
    },
    {
        "id": "PWD-MH-2026-WTR-88",
        "filename": "benchmark_04_mahapwd_bulk_water_esr.pdf",
        "authority": "MAHARASHTRA PUBLIC WORKS & JAL JEEVAN MISSION",
        "division": "EXECUTIVE ENGINEER, PUBLIC HEALTH WORKS DIVISION SOLAPUR",
        "work_name": "Augmentation of Regional Water Supply Scheme: DI Transmission Main, Pump House, and 5 Elevated Storage Reservoirs (ESR)",
        "nit_no": "NIT-2026/PWD-PH/SOL/WTR-88",
        "tender_id": "2026_PWD_61209_1",
        "estimated_cost_str": "Rs. 16,75,00,000/- (Rupees Sixteen Crores Seventy-Five Lakhs only)",
        "estimated_cost_val": 167500000.0,
        "emd_str": "Rs. 16,75,000/- (1% of Estimated Cost)",
        "tender_fee_str": "Rs. 8,000/-",
        "turnover_clause": "Average annual turnover of minimum Rs. 8.38 Crores (50%) in last 3 financial years.",
        "solvency_clause": "Bank Solvency certificate of Rs. 6.70 Crores (40%) from any recognized bank.",
        "similar_work_clause": "Experience in laying DI/MS bulk water pipeline and construction of minimum 2 RCC overhead tanks (ESR) worth Rs. 13.40 Cr.",
        "contractor_class": "Class II or higher PWD / Water Resources",
        "completion_period": "14 Months",
        "dlp": "24 Months",
        "bid_validity": "120 Days",
        "machinery": ["2 Hydraulic Excavators", "1 Mobile Crane (15T)", "Pipe Testing Pump Equipment", "Electric Welding Generators"]
    },
    {
        "id": "PWD-MH-2026-RRL-204",
        "filename": "benchmark_05_mahapwd_rural_roads_pmgsy.pdf",
        "authority": "MAHARASHTRA RURAL ROADS DEVELOPMENT ASSOCIATION (MRRDA / PWD)",
        "division": "EXECUTIVE ENGINEER, PWD PMGSY DIVISION NAGPUR",
        "work_name": "Construction and 5-Year Routine Maintenance of Rural Connectivity Road Network under PMGSY-III in Umred Block",
        "nit_no": "e-Procurement Notice No. MRRDA/NGP/2026/204",
        "tender_id": "2026_MRRDA_44190_1",
        "estimated_cost_str": "Rs. 14,20,00,000/- (Rupees Fourteen Crores Twenty Lakhs only)",
        "estimated_cost_val": 142000000.0,
        "emd_str": "Rs. 28,40,000/- (2% of Cost as Bid Security)",
        "tender_fee_str": "Rs. 5,000/-",
        "turnover_clause": "Average annual turnover not less than Rs. 7.10 Crores (50%) over the last 3 financial years.",
        "solvency_clause": "Bank solvency certificate of minimum Rs. 5.68 Crores (40%) from a scheduled bank.",
        "similar_work_clause": "Satisfactorily completed similar rural/highway road construction works of Rs. 11.36 Cr (80%) or two works of Rs. 7.10 Cr (50%).",
        "contractor_class": "Class II (Civil) or higher registered contractor",
        "completion_period": "12 Months (Construction) + 60 Months (Routine Maintenance)",
        "dlp": "60 Months (5 Years DLP under PMGSY)",
        "bid_validity": "90 Days",
        "machinery": ["1 Wet Mix Macadam (WMM) Plant (60 TPH)", "1 Paver Finisher", "2 Static Rollers", "1 Water Tanker (6000L)"]
    },

    # 2. CPWD (Central Public Works Department)
    {
        "id": "CPWD-2026-MED-012",
        "filename": "benchmark_06_cpwd_medical_college_hospital.pdf",
        "authority": "CENTRAL PUBLIC WORKS DEPARTMENT (CPWD), GOVERNMENT OF INDIA",
        "division": "OFFICE OF THE CHIEF ENGINEER, DELHI ZONE-IV, CPWD",
        "work_name": "Turnkey EPC Construction of 500-Bedded Super-Specialty Hospital Complex with Medical College at Alwar",
        "nit_no": "NIT No. 12/CE/DZ-IV/CPWD/2026-27",
        "tender_id": "2026_CPWD_99214_1",
        "estimated_cost_str": "Rs. 64,20,00,000/- (Rupees Sixty-Four Crores Twenty Lakhs only)",
        "estimated_cost_val": 642000000.0,
        "emd_str": "Rs. 74,20,000/- (Rs. 20 Lakhs + 1% of balance exceeding Rs. 10 Cr as per CPWD manual)",
        "tender_fee_str": "Nil (e-Tendering Portal Free Download)",
        "turnover_clause": "The average annual financial turnover on construction works should be at least 50% of the estimated cost (Rs. 32.10 Crores) during the immediate last 3 consecutive financial years.",
        "solvency_clause": "Bankers Certificate / Bank Solvency Certificate of minimum 40% of estimated cost (Rs. 25.68 Crores) or Net Worth certificate of 10% (Rs. 6.42 Cr).",
        "similar_work_clause": "Experience in successfully completed hospital / institutional building works during last 7 years: One work of Rs. 51.36 Cr (80%), or Two works of Rs. 38.52 Cr (60%), or Three works of Rs. 25.68 Cr (40%).",
        "contractor_class": "CPWD Class Super (B&R) or equivalent Central Govt enlistment",
        "completion_period": "24 Months",
        "dlp": "60 Months (5 Years Comprehensive Warranty for Medical Infrastructure)",
        "bid_validity": "75 Days",
        "machinery": ["2 Tower Cranes (50m)", "2 Concrete Batching Plants (30m3/hr)", "4 Transit Mixers", "Fully equipped MEP and HVAC commissioning tools"]
    },
    {
        "id": "CPWD-2026-HSG-088",
        "filename": "benchmark_07_cpwd_residential_colony.pdf",
        "authority": "CENTRAL PUBLIC WORKS DEPARTMENT (CPWD)",
        "division": "EXECUTIVE ENGINEER, BANGALORE CENTRAL DIVISION-II",
        "work_name": "Construction of Central Government General Pool Residential Accommodation (GPRA) Type-IV & Type-V Flats (180 Units)",
        "nit_no": "NIT No. 88/EE/BCD-II/2026",
        "tender_id": "2026_CPWD_78103_4",
        "estimated_cost_str": "Rs. 32,50,00,000/- (Rupees Thirty-Two Crores Fifty Lakhs only)",
        "estimated_cost_val": 325000000.0,
        "emd_str": "Rs. 42,50,000/- (Calculated as per CPWD Works Manual 2024)",
        "tender_fee_str": "Nil",
        "turnover_clause": "Average annual turnover of at least Rs. 16.25 Crores (50% of estimated cost) over the last 3 financial years.",
        "solvency_clause": "Bank solvency of minimum Rs. 13.00 Crores (40%) from any Nationalized or Scheduled bank.",
        "similar_work_clause": "Completed residential multistory building works: One work of Rs. 26.00 Cr (80%) or two works of Rs. 16.25 Cr (50%).",
        "contractor_class": "Class I (B&R) CPWD",
        "completion_period": "15 Months",
        "dlp": "36 Months",
        "bid_validity": "90 Days",
        "machinery": ["1 Passenger Hoist", "1 Tower Crane", "Aluminium Formwork System (Mivan type)", "Concrete boom placers"]
    },
    {
        "id": "CPWD-2026-AVN-034",
        "filename": "benchmark_08_cpwd_airport_apron_pavement.pdf",
        "authority": "CENTRAL PUBLIC WORKS DEPARTMENT / AIRPORTS PROJECT WING",
        "division": "CHIEF ENGINEER (CIVIL AVIATION), CPWD NEW DELHI",
        "work_name": "Extension of Rigid Pavement Apron, Construction of 4 Code-E Aircraft Parking Bays and Taxiway Track",
        "nit_no": "NIT Ref. CPWD/AVN/2026/034",
        "tender_id": "2026_CPWD_55321_1",
        "estimated_cost_str": "Rs. 54,00,00,000/- (Rupees Fifty-Four Crores only)",
        "estimated_cost_val": 540000000.0,
        "emd_str": "Rs. 64,00,000/-",
        "tender_fee_str": "Nil",
        "turnover_clause": "Annual financial turnover not less than Rs. 27.00 Crores (50%) in last 3 financial years.",
        "solvency_clause": "Bank Solvency Certificate of Rs. 21.60 Crores (40% of estimated cost).",
        "similar_work_clause": "Rigid pavement / Paving Quality Concrete (PQC) runway or expressway experience: One work of Rs. 43.20 Cr or two works of Rs. 27.00 Cr.",
        "contractor_class": "Class Super or Class I (Civil Heavy Airfield Works)",
        "completion_period": "12 Months",
        "dlp": "36 Months",
        "bid_validity": "90 Days",
        "machinery": ["1 Fixed Form or Slip Form Paving Machine (PQC)", "1 Concrete Batching Plant (90 m3/hr)", "6 Transit Mixers", "Joint Cutting & Sealing Machines"]
    },
    {
        "id": "CPWD-2026-HER-019",
        "filename": "benchmark_09_cpwd_heritage_conservation.pdf",
        "authority": "CENTRAL PUBLIC WORKS DEPARTMENT (HERITAGE WING)",
        "division": "EXECUTIVE ENGINEER, HERITAGE RESTORATION DIVISION MUMBAI",
        "work_name": "Comprehensive Conservation, Seismic Retrofitting, and Adaptive Restoration of Historic High Court Annex Stone Building",
        "nit_no": "e-NIT No. CPWD/HER/MUM/2026/19",
        "tender_id": "2026_CPWD_41098_1",
        "estimated_cost_str": "Rs. 22,10,00,000/- (Rupees Twenty-Two Crores Ten Lakhs only)",
        "estimated_cost_val": 221000000.0,
        "emd_str": "Rs. 32,10,000/-",
        "tender_fee_str": "Nil",
        "turnover_clause": "Average annual turnover of minimum Rs. 11.05 Crores (50%) in last 3 financial years.",
        "solvency_clause": "Bank Solvency of Rs. 8.84 Crores (40%).",
        "similar_work_clause": "Experience in specialized stone masonry conservation, lime-plaster mortar restoration, and seismic retrofitting of heritage monuments: One work of Rs. 17.68 Cr or two works of Rs. 11.05 Cr.",
        "contractor_class": "Special Class Heritage Enlisted Contractor",
        "completion_period": "18 Months",
        "dlp": "36 Months",
        "bid_validity": "120 Days",
        "machinery": ["Low-pressure Grouting Pumps", "Diamond Core Drilling equipment", "Micro-sandblasting restoration machines", "Cup-lock heavy scaffolding"]
    },
    {
        "id": "CPWD-2026-DTC-042",
        "filename": "benchmark_10_cpwd_national_data_center.pdf",
        "authority": "CENTRAL PUBLIC WORKS DEPARTMENT & MINISTRY OF ELECTRONICS & IT",
        "division": "CHIEF ENGINEER (ELECTRICAL & SPECIAL PROJECTS), CPWD HYDERABAD",
        "work_name": "Civil, Structural and High-Density MEP Construction for National Data Center Tier-III Facility (10 MW IT Load)",
        "nit_no": "NIT No. CPWD/NDC/HYD/2026/042",
        "tender_id": "2026_CPWD_89412_5",
        "estimated_cost_str": "Rs. 88,50,00,000/- (Rupees Eighty-Eight Crores Fifty Lakhs only)",
        "estimated_cost_val": 885000000.0,
        "emd_str": "Rs. 98,50,000/-",
        "tender_fee_str": "Nil",
        "turnover_clause": "Average annual turnover of at least Rs. 44.25 Crores (50%) in last 3 consecutive financial years.",
        "solvency_clause": "Bank solvency of minimum Rs. 35.40 Crores (40%) or Net Worth of Rs. 8.85 Cr.",
        "similar_work_clause": "Execution of mission-critical Data Centers (Tier III/IV) or high-density telecom complexes: One work of Rs. 70.80 Cr or two works of Rs. 44.25 Cr.",
        "contractor_class": "Class Super (Composite Civil & Electrical) CPWD",
        "completion_period": "16 Months",
        "dlp": "60 Months",
        "bid_validity": "90 Days",
        "machinery": ["Precision HVAC balancing kits", "Thermal imaging diagnostics", "500 kVA testing load banks", "Heavy lifting gantries"]
    },

    # 3. NHAI (National Highways Authority of India)
    {
        "id": "NHAI-2026-HAM-EXP-08",
        "filename": "benchmark_11_nhai_greenfield_expressway_ham.pdf",
        "authority": "NATIONAL HIGHWAYS AUTHORITY OF INDIA (NHAI), MINISTRY OF ROAD TRANSPORT & HIGHWAYS",
        "division": "REGIONAL OFFICE, NHAI NAGPUR",
        "work_name": "Construction of 4-Lane Greenfield Expressway from Km 48.000 to Km 108.000 on Hybrid Annuity Mode (HAM)",
        "nit_no": "RFP / Bid Document No. NHAI/RO/NGP/EXP/2026/PKG-08",
        "tender_id": "2026_NHAI_11204_1",
        "estimated_cost_str": "Rs. 245,00,00,000/- (Rupees Two Hundred Forty-Five Crores only)",
        "estimated_cost_val": 2450000000.0,
        "emd_str": "Rs. 2,45,00,000/- (1% of Estimated Cost as Bid Security Bank Guarantee)",
        "tender_fee_str": "Rs. 50,000/- plus 18% GST (e-Tender Processing Fee)",
        "turnover_clause": "The bidder shall have a minimum Net Worth of Rs. 24.50 Crores (10% of Cost) and average annual turnover of Rs. 122.50 Crores (50%) in last 3 financial years.",
        "solvency_clause": "Credit Facility / Bank Solvency Certificate of Rs. 98.00 Crores (40% of Estimated Project Cost).",
        "similar_work_clause": "Experience in National/State 4-Lane Highway / Expressway projects: One similar work of Rs. 196.00 Cr (80%), or Two works of Rs. 122.50 Cr (50%), or Three works of Rs. 98.00 Cr (40%).",
        "contractor_class": "Tier-1 Infrastructure EPC / HAM Bidder",
        "completion_period": "30 Months",
        "dlp": "60 Months (5 Years Mandatory Maintenance under HAM)",
        "bid_validity": "180 Days",
        "machinery": ["2 Slipform Concrete Pavers (SP-500)", "2 Hot Mix Plants (160 TPH)", "4 Motor Graders (160 HP)", "6 Vibratory Rollers"]
    },
    {
        "id": "NHAI-2026-ELV-CORR-14",
        "filename": "benchmark_12_nhai_elevated_corridor.pdf",
        "authority": "NATIONAL HIGHWAYS AUTHORITY OF INDIA",
        "division": "PROJECT IMPLEMENTATION UNIT (PIU) THANE",
        "work_name": "Construction of 6-Lane Elevated Flyover Corridor from Fountain Hotel to Gaimukh with Precast Segmental Box Girders",
        "nit_no": "e-NIT No. NHAI/PIU-THN/ELV/2026/14",
        "tender_id": "2026_NHAI_76129_2",
        "estimated_cost_str": "Rs. 178,00,00,000/- (Rupees One Hundred Seventy-Eight Crores only)",
        "estimated_cost_val": 1780000000.0,
        "emd_str": "Rs. 1,78,00,000/-",
        "tender_fee_str": "Rs. 25,000/-",
        "turnover_clause": "Average annual financial turnover shall not be less than Rs. 89.00 Crores (50%) in preceding 3 financial years.",
        "solvency_clause": "Bank solvency certificate of minimum Rs. 71.20 Crores (40%) issued within 6 months.",
        "similar_work_clause": "Completed segmental elevated bridge / viaduct works: One work of Rs. 142.40 Cr (80%) or two works of Rs. 89.00 Cr (50%).",
        "contractor_class": "Tier-1 Bridge / Elevated Viaduct EPC Contractor",
        "completion_period": "24 Months",
        "dlp": "36 Months",
        "bid_validity": "120 Days",
        "machinery": ["1 Segment Launching Gantry (120T)", "2 Rotary Piling Rigs", "1 Precast Casting Yard setup with 4 casting beds", "2 Heavy Trailer Trucks"]
    },
    {
        "id": "NHAI-2026-ITS-ATMS-03",
        "filename": "benchmark_13_nhai_smart_its_atms.pdf",
        "authority": "NATIONAL HIGHWAYS AUTHORITY OF INDIA (ITS DIVISION)",
        "division": "PIU EXPRESSWAYS, DWARKA NEW DELHI",
        "work_name": "Supply, Installation, Testing, and Commissioning of Advanced Traffic Management System (ATMS) & AI Surveillance on NH-48",
        "nit_no": "NIT No. NHAI/ITS/ATMS/2026/03",
        "tender_id": "2026_NHAI_33201_1",
        "estimated_cost_str": "Rs. 19,60,00,000/- (Rupees Nineteen Crores Sixty Lakhs only)",
        "estimated_cost_val": 196000000.0,
        "emd_str": "Rs. 19,60,000/- (1% of Estimated Cost)",
        "tender_fee_str": "Rs. 10,000/-",
        "turnover_clause": "Average annual turnover of minimum Rs. 9.80 Crores (50%) in last 3 financial years.",
        "solvency_clause": "Bank Solvency of Rs. 7.84 Crores (40%).",
        "similar_work_clause": "Experience in Highway ATMS / Smart Toll System / Optical Fiber Infrastructure: One work of Rs. 15.68 Cr or two works of Rs. 9.80 Cr.",
        "contractor_class": "Specialist ITS & Highway Telecom Integrator",
        "completion_period": "9 Months",
        "dlp": "36 Months (Including Comprehensive O&M)",
        "bid_validity": "90 Days",
        "machinery": ["Optical Time Domain Reflectometers (OTDR)", "Fiber Splicing Machines", "Bucket Trucks for VMS & Camera mounting", "Network Analyzer suites"]
    },
    {
        "id": "NHAI-2026-TNL-NATM-07",
        "filename": "benchmark_14_nhai_ghat_twin_tunnel.pdf",
        "authority": "NATIONAL HIGHWAYS AUTHORITY OF INDIA",
        "division": "PIU HILL ROADS & TUNNELS, DEHRADUN",
        "work_name": "Construction of Twin-Tube 2-Lane Highway Tunnels (Length 2.4 Km each) by NATM Method including Ventilation and Fire Safety",
        "nit_no": "RFP No. NHAI/TUNNEL/GHAT/2026/07",
        "tender_id": "2026_NHAI_98112_4",
        "estimated_cost_str": "Rs. 310,00,00,000/- (Rupees Three Hundred Ten Crores only)",
        "estimated_cost_val": 3100000000.0,
        "emd_str": "Rs. 3,10,00,000/-",
        "tender_fee_str": "Rs. 50,000/-",
        "turnover_clause": "Average annual financial turnover exceeding Rs. 155.00 Crores (50%) in preceding 3 financial years.",
        "solvency_clause": "Bank Solvency Certificate of Rs. 124.00 Crores (40% of Project Cost).",
        "similar_work_clause": "Completed drill-and-blast or NATM vehicular road tunnel of minimum 1.5 km: One work of Rs. 248.00 Cr (80%) or two works of Rs. 155.00 Cr (50%).",
        "contractor_class": "Tier-1 International / National Heavy Tunneling Contractor",
        "completion_period": "36 Months",
        "dlp": "60 Months",
        "bid_validity": "180 Days",
        "machinery": ["2 Computerized Two-Boom / Three-Boom Jumbo Drills", "2 Robotic Shotcrete Spraying Machines", "4 Underground Dump Trucks (30T)", "Ventilation Fans & Scrubbers"]
    },
    {
        "id": "NHAI-2026-CBL-BRG-22",
        "filename": "benchmark_15_nhai_cable_stayed_bridge.pdf",
        "authority": "NATIONAL HIGHWAYS AUTHORITY OF INDIA",
        "division": "PIU MARINE & COASTAL HIGHWAYS, KOCHI",
        "work_name": "Engineering, Procurement and Construction (EPC) of 4-Lane Iconic Cable-Stayed Bridge across Coastal Estuary (Span 350m)",
        "nit_no": "e-Procurement Notice NHAI/CBL/2026/PKG-22",
        "tender_id": "2026_NHAI_66540_1",
        "estimated_cost_str": "Rs. 415,00,00,000/- (Rupees Four Hundred Fifteen Crores only)",
        "estimated_cost_val": 4150000000.0,
        "emd_str": "Rs. 4,15,00,000/- (1% of Estimated Cost)",
        "tender_fee_str": "Rs. 50,000/-",
        "turnover_clause": "Bidder must demonstrate average annual turnover of at least Rs. 207.50 Crores (50%) in last 3 financial years.",
        "solvency_clause": "Bank solvency certificate of minimum Rs. 166.00 Crores (40%) issued by a leading commercial bank.",
        "similar_work_clause": "Completed major long-span Cable Stayed or Extradosed Bridge: One work of Rs. 332.00 Cr (80%) or two works of Rs. 207.50 Cr (50%).",
        "contractor_class": "Global / National Specialized Bridge EPC Contractor",
        "completion_period": "36 Months",
        "dlp": "60 Months (5 Years Maintenance and Health Monitoring)",
        "bid_validity": "180 Days",
        "machinery": ["Stay Cable Jacking & Tensioning Equipment", "Floating Concrete Batching Plant", "Marine Jack-Up Barges", "Heavy Lift Derrick Cranes"]
    }
]


def build_pdf_document(spec: dict, output_path: Path):
    """Builds a rich multi-page authentic tender PDF document."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        alignment=1, # Center
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        alignment=1,
        textColor=colors.HexColor('#334155'),
        spaceAfter=12
    )
    h1_style = ParagraphStyle(
        'DocH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#334155'),
        leftIndent=15,
        spaceAfter=3
    )

    story = []

    # ---------------- PAGE 1: COVER & NOTICE INVITING TENDER (NIT) ----------------
    story.append(Paragraph(spec['authority'], title_style))
    story.append(Paragraph(spec['division'], subtitle_style))
    story.append(Spacer(1, 10))

    # Header Banner Table
    banner_data = [
        [Paragraph(f"<b>{spec['nit_no']}</b>", ParagraphStyle('B1', fontName='Helvetica-Bold', fontSize=10, textColor=colors.white)),
         Paragraph(f"<b>Tender ID: {spec['tender_id']}</b>", ParagraphStyle('B2', fontName='Helvetica-Bold', fontSize=10, textColor=colors.white, alignment=2))]
    ]
    banner_table = Table(banner_data, colWidths=[320, 180])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1e3a8a')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("SECTION I: DETAILED NOTICE INVITING e-TENDER (NIT)", h1_style))
    story.append(Paragraph(
        f"Online percentage rate / item rate tenders in two-cover bid system (Cover-1: Technical Bid, Cover-2: Financial Bid) "
        f"are invited on behalf of the {spec['authority']} from enlisted, experienced, and eligible contractors meeting the criteria specified herein.",
        body_style
    ))

    # Core Parameters Table
    param_data = [
        [Paragraph("<b>Item / Parameter</b>", body_style), Paragraph("<b>Tender Specification Value</b>", body_style)],
        [Paragraph("<b>1. Name of Work:</b>", body_style), Paragraph(spec['work_name'], body_style)],
        [Paragraph("<b>2. Estimated Cost of Work:</b>", body_style), Paragraph(f"<b>{spec['estimated_cost_str']}</b>", body_style)],
        [Paragraph("<b>3. Earnest Money Deposit (EMD):</b>", body_style), Paragraph(spec['emd_str'], body_style)],
        [Paragraph("<b>4. Cost of Tender Document:</b>", body_style), Paragraph(spec['tender_fee_str'], body_style)],
        [Paragraph("<b>5. Contract Completion Period:</b>", body_style), Paragraph(f"<b>{spec['completion_period']}</b>", body_style)],
        [Paragraph("<b>6. Defect Liability Period (DLP):</b>", body_style), Paragraph(f"<b>{spec['dlp']}</b>", body_style)],
        [Paragraph("<b>7. Eligible Contractor Class:</b>", body_style), Paragraph(spec['contractor_class'], body_style)],
        [Paragraph("<b>8. Bid Validity Period:</b>", body_style), Paragraph(spec['bid_validity'], body_style)],
    ]
    param_table = Table(param_data, colWidths=[170, 330])
    param_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(param_table)
    story.append(Spacer(1, 14))

    # ---------------- PAGE 2: KEY DATES & TIMELINE ----------------
    story.append(PageBreak())
    story.append(Paragraph("SECTION II: TENDER TIMELINE AND MILESTONES SCHEDULE", h1_style))
    story.append(Paragraph(
        "Bidders are requested to strictly adhere to the critical dates indicated below. All times specified are in Indian Standard Time (IST).",
        body_style
    ))

    schedule_data = [
        [Paragraph("<b>Milestone Stage</b>", body_style), Paragraph("<b>Date & Time (IST)</b>", body_style), Paragraph("<b>Action Required</b>", body_style)],
        [Paragraph("1. Document Download Start Date", body_style), Paragraph("01-11-2026 10:00 hrs", body_style), Paragraph("Download RFP & BOQ from portal", body_style)],
        [Paragraph("2. Pre-Bid Conference Date", body_style), Paragraph("08-11-2026 at 11:30 hrs", body_style), Paragraph("Submit queries in writing", body_style)],
        [Paragraph("3. Clarifications & Addenda Release", body_style), Paragraph("12-11-2026 17:00 hrs", body_style), Paragraph("Official responses published", body_style)],
        [Paragraph("4. Bid Submission Start Date", body_style), Paragraph("13-11-2026 10:00 hrs", body_style), Paragraph("Upload encrypted digital bids", body_style)],
        [Paragraph("5. Last Date & Time of Online Submission", body_style), Paragraph("<b>24-11-2026 upto 17:00 hrs</b>", body_style), Paragraph("Final bid closure (Strict cutoff)", body_style)],
        [Paragraph("6. Date of Technical Bid Opening", body_style), Paragraph("<b>25-11-2026 at 15:00 hrs</b>", body_style), Paragraph("Cover-1 opening in division office", body_style)],
        [Paragraph("7. Financial Bid Opening Date", body_style), Paragraph("To be notified post technical evaluation", body_style), Paragraph("Cover-2 for qualified bidders only", body_style)],
    ]
    sched_table = Table(schedule_data, colWidths=[170, 150, 180])
    sched_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(sched_table)
    story.append(Spacer(1, 14))

    # ---------------- PAGE 3: ELIGIBILITY & QUALIFICATION CRITERIA ----------------
    story.append(PageBreak())
    story.append(Paragraph("SECTION III: ELIGIBILITY & QUALIFICATION CRITERIA (COVER-1)", h1_style))
    story.append(Paragraph(
        "Only those contractors who fulfill the following minimum financial and technical eligibility criteria shall be considered for technical qualification. Bids failing any mandatory requirement will be rejected outright.",
        body_style
    ))

    # Clause 3.1
    story.append(Paragraph("Clause 3.1: Enlistment and Contractor Registration", h2_style))
    story.append(Paragraph(
        f"The contractor must possess valid active registration certificate in <b>{spec['contractor_class']}</b>. "
        f"Self-attested copy of registration renewal valid up to completion date must be enclosed in Technical Envelope.",
        body_style
    ))

    # Clause 3.2
    story.append(Paragraph("Clause 3.2: Statutory Registrations and Tax Compliance", h2_style))
    story.append(Paragraph(
        "Bidder must submit certified proof of: "
        "(a) Valid Goods and Services Tax Identification Number (GSTIN) with proof of latest GSTR-3B return; "
        "(b) Permanent Account Number (PAN) Card issued by Income Tax Department; "
        "(c) Employees' Provident Fund (EPF) registration code and latest challan; "
        "(d) Active Employees State Insurance Corporation (ESIC) registration where applicable.",
        body_style
    ))

    # Clause 3.3
    story.append(Paragraph("Clause 3.3: Non-Debarment and Non-Blacklisting Affidavit", h2_style))
    story.append(Paragraph(
        "The bidder must submit an original Affidavit on Non-Judicial Stamp Paper of Rs. 100/- duly notarized, stating that "
        "the firm / contractor has not been blacklisted, debarred, or banned by any Central / State Government Department, Public Sector Undertaking, or Local Body as on the date of bid submission.",
        body_style
    ))

    # Clause 4.1: Financial Turnover
    story.append(Paragraph("Clause 4.1: Average Annual Financial Turnover", h2_style))
    story.append(Paragraph(
        f"<b>{spec['turnover_clause']}</b> "
        f"Audited Balance Sheets and Profit & Loss accounts certified by a registered Chartered Accountant with Unique Document Identification Number (UDIN) must be uploaded.",
        body_style
    ))

    # Clause 4.2: Bank Solvency
    story.append(Paragraph("Clause 4.2: Financial Solvency / Banker's Certificate", h2_style))
    story.append(Paragraph(
        f"<b>{spec['solvency_clause']}</b> "
        f"The Solvency Certificate must be dated not earlier than 6 months prior to the date of publication of this NIT and strictly in the prescribed Form-B format.",
        body_style
    ))

    # ---------------- PAGE 4: TECHNICAL EXPERIENCE & MACHINERY ----------------
    story.append(PageBreak())
    story.append(Paragraph("SECTION IV: TECHNICAL EXPERIENCE AND WORK CREDENTIALS", h1_style))
    
    # Clause 5.1
    story.append(Paragraph("Clause 5.1: Similar Work Experience Criteria", h2_style))
    story.append(Paragraph(
        f"<b>{spec['similar_work_clause']}</b> "
        f"Work experience certificates must be signed by an officer not below the rank of Executive Engineer or Project Director and must state clearly the project value, start date, and completion date.",
        body_style
    ))

    # Clause 5.2: Plant & Machinery
    story.append(Paragraph("Clause 5.2: Minimum Plant, Machinery, and Equipment Holding", h2_style))
    story.append(Paragraph(
        "The bidder must demonstrate ownership or legally binding leasehold agreement for the minimum fleet of plant and machinery required for timely execution:",
        body_style
    ))
    for m in spec['machinery']:
        story.append(Paragraph(f"• <b>{m}</b>", bullet_style))

    story.append(Spacer(1, 10))

    # Clause 5.3: Available Bid Capacity
    story.append(Paragraph("Clause 5.3: Available Bid Capacity Assessment", h2_style))
    story.append(Paragraph(
        "Bidders must possess available bid capacity greater than the estimated cost of work. "
        "Calculated as: <i>Available Bid Capacity = (A * N * 2) - B</i>, where A = Maximum value of civil works executed in any one year during last 5 years, "
        "N = Number of years prescribed for completion, and B = Value of existing commitments.",
        body_style
    ))

    # Clause 6.1: Submission Checklist
    story.append(Paragraph("Clause 6.1: Mandatory Cover-1 Submission Checklist", h2_style))
    checklist_items = [
        "Receipt of Online EMD & Tender Fee payment",
        "Valid Enlistment Order & Class Registration",
        "GSTIN, PAN, and EPF Registration Certificates",
        "Non-Blacklisting Notarized Affidavit on Stamp Paper",
        "CA Certified Turnover Certificates with UDIN for FY 22-23, FY 23-24, FY 24-25",
        "Bank Solvency Certificate in original bank format",
        "Client Completion Certificates for qualifying similar works",
        "Plant & Machinery ownership / lease affidavits"
    ]
    for idx, item in enumerate(checklist_items, 1):
        story.append(Paragraph(f"[  ] Document #{idx}: {item}", bullet_style))

    doc.build(story, canvasmaker=NumberedCanvas)


def generate_all_benchmarks():
    """Generates all 15 benchmark PDFs and creates a metadata catalog."""
    out_dir = Path("d:/projects/project 1/DOTS AI AGENT/data/benchmark_tenders")
    out_dir.mkdir(parents=True, exist_ok=True)

    catalog = []
    print(f"Generating {len(BENCHMARK_SPECIFICATIONS)} benchmark tender PDFs in {out_dir}...")

    for spec in BENCHMARK_SPECIFICATIONS:
        pdf_path = out_dir / spec['filename']
        build_pdf_document(spec, pdf_path)
        print(f"  [+] Created: {spec['filename']} ({spec['id']} - Rs. {spec['estimated_cost_val']/10000000:.2f} Cr)")
        
        catalog.append({
            "id": spec["id"],
            "filename": spec["filename"],
            "authority": spec["authority"],
            "division": spec["division"],
            "work_name": spec["work_name"],
            "nit_no": spec["nit_no"],
            "tender_id": spec["tender_id"],
            "estimated_cost_inr": spec["estimated_cost_val"],
            "estimated_cost_str": spec["estimated_cost_str"],
            "contractor_class": spec["contractor_class"],
            "completion_period": spec["completion_period"],
            "dlp": spec["dlp"],
            "bid_validity": spec["bid_validity"],
            "calibration_focus": "Multi-tier turnover, bank solvency, and similar work criteria"
        })

    catalog_path = out_dir / "manifest.json"
    catalog_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    print(f"Successfully generated 15 benchmark tenders and manifest.json.")


if __name__ == "__main__":
    generate_all_benchmarks()
