from hire_signal.filters import clasificar
from hire_signal.spiders.base import _texto


def test_titulo():
    assert clasificar("Senior Backend Engineer")["seniority"] == "senior"
    assert clasificar("Mid-Market Sales Engineer")["seniority"] == "unknown"


def test_niveles_con_puntuacion_y_pt():
    assert clasificar("Product Manager II, Search")["seniority"] == "mid"
    assert clasificar("Analista Pleno de Dados")["seniority"] == "mid"
    assert clasificar("Gerente de Automatización")["seniority"] == "lead"


def test_anios_en_descripcion_html_escapado():
    d = _texto("&lt;p&gt;We need 5+ years of experience&lt;/p&gt;")
    assert clasificar("Software Engineer", d)["seniority"] == "senior"
    d = _texto("<li>1+ years building APIs</li>")
    assert clasificar("Software Engineer", d)["seniority"] == "junior"


def test_roles_no_tecnicos():
    assert clasificar("Procurement Specialist")["role_category"] == "operations"
    assert clasificar("Senior Counsel, Employment")["role_category"] == "legal"
    assert clasificar("Credit Risk Analyst")["role_category"] == "finance"
    assert clasificar("Sr. Client Partner, Pharma")["role_category"] == "sales"


def test_ingenieria_no_cae_en_legal_ni_operaciones():
    assert clasificar("Staff Software Engineer, Payments Compliance")["role_category"] == "backend"
    assert clasificar("Commercial Customer Success Manager")["role_category"] == "support"
