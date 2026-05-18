from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from personeros.models import Personero, PerfilUsuario

class PersoneroExportTestCase(TestCase):
    def setUp(self):
        # Crear un superadministrador
        self.admin_user = User.objects.create_user(username='admin_test', password='password123')
        self.admin_profile = PerfilUsuario.objects.create(usuario=self.admin_user, rol='superadmin')

        # Crear un personero de prueba (la señal crear_usuario_personero se encargará del User y del PerfilUsuario)
        self.personero = Personero.objects.create(
            dni='12345678',
            nombres='Eduardo',
            apellido_paterno='Herrera',
            apellido_materno='Ayay',
            nro_celular='987654321',
            estado='confirmado'
        )
        self.personero_user = self.personero.usuario

        self.client = Client()

    def test_export_anonymous_redirects_to_login(self):
        """Verifica que un usuario no autenticado sea redirigido al login."""
        url = reverse('personeros:exportar_excel')
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('personeros:login')}?next={url}")

    def test_export_personero_role_redirects_to_profile(self):
        """Verifica que un personero común no pueda exportar y sea redirigido a su perfil."""
        self.client.login(username='12345678', password='12345678')
        response = self.client.get(reverse('personeros:exportar_excel'))
        self.assertRedirects(response, reverse('personeros:mi_perfil'))

    def test_export_admin_success(self):
        """Verifica que un administrador pueda descargar el CSV correctamente con UTF-8 BOM y datos correctos."""
        self.client.login(username='admin_test', password='password123')
        response = self.client.get(reverse('personeros:exportar_excel'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertTrue(response['Content-Disposition'].startswith('attachment; filename="personeros_export_'))

        # Obtener el contenido crudo
        content = response.content

        # Verificar presencia del UTF-8 BOM (\xef\xbb\xbf)
        self.assertTrue(content.startswith(b'\xef\xbb\xbf'))

        # Decodificar el contenido (omitiendo el BOM)
        csv_text = content[3:].decode('utf-8')

        # Verificar cabeceras y delimitador punto y coma (;)
        headers = csv_text.split('\r\n')[0]
        self.assertIn('DNI;Apellido Paterno;Apellido Materno;Nombres', headers)

        # Verificar que el registro del personero está en el archivo (los datos personales se guardan automáticamente en mayúsculas)
        self.assertIn('12345678;HERRERA;AYAY;EDUARDO', csv_text)

    def test_export_admin_with_filters(self):
        """Verifica que la exportación respete los filtros GET activos."""
        # Agregar otro personero que sea de un estado diferente
        Personero.objects.create(
            dni='87654321',
            nombres='Carlos',
            apellido_paterno='Pérez',
            apellido_materno='Gómez',
            nro_celular='999999999',
            estado='pendiente'
        )

        self.client.login(username='admin_test', password='password123')

        # Filtrar por estado 'pendiente'
        response = self.client.get(reverse('personeros:exportar_excel'), {'estado': 'pendiente'})
        csv_text = response.content[3:].decode('utf-8')

        # El de DNI 87654321 debe estar presente (en mayúsculas)
        self.assertIn('87654321;PÉREZ;GÓMEZ;CARLOS', csv_text)
        # El de DNI 12345678 (confirmado) NO debe estar presente
        self.assertNotIn('12345678;HERRERA;AYAY;EDUARDO', csv_text)


from personeros.forms import PersoneroPublicRegistrationForm

class PersoneroRegistrationFormTestCase(TestCase):
    def test_form_valid_with_only_required_fields(self):
        """Verifica que el formulario es válido cuando solo se ingresan los campos obligatorios."""
        data = {
            'apellido_paterno': 'Herrera',
            'apellido_materno': 'Ayay',
            'nombres': 'Eduardo',
            'dni': '99998888',
            'nro_celular': '987654321',
        }
        form = PersoneroPublicRegistrationForm(data=data)
        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_form_invalid_if_missing_required_fields(self):
        """Verifica que el formulario es inválido si falta alguno de los obligatorios."""
        # Falta celular
        data = {
            'apellido_paterno': 'Herrera',
            'apellido_materno': 'Ayay',
            'nombres': 'Eduardo',
            'dni': '99998888',
        }
        form = PersoneroPublicRegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('nro_celular', form.errors)

    def test_form_cleans_cellular_correctly(self):
        """Verifica que el validador de celular limpie espacios y guiones y guarde el formato limpio."""
        data = {
            'apellido_paterno': 'Herrera',
            'apellido_materno': 'Ayay',
            'nombres': 'Eduardo',
            'dni': '99997777',
            'nro_celular': '987 - 654 - 321', # con espacios y guiones
        }
        form = PersoneroPublicRegistrationForm(data=data)
        self.assertTrue(form.is_valid(), form.errors.as_json())
        self.assertEqual(form.cleaned_data['nro_celular'], '987654321')

    def test_form_invalid_if_invalid_cellular_format(self):
        """Verifica que no se acepten celulares que no tengan 9 dígitos o no empiecen con 9."""
        # Empieza con 8
        data = {
            'apellido_paterno': 'Herrera',
            'apellido_materno': 'Ayay',
            'nombres': 'Eduardo',
            'dni': '99996666',
            'nro_celular': '887654321',
        }
        form = PersoneroPublicRegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('nro_celular', form.errors)

        # Menos dígitos
        data['nro_celular'] = '987654'
        form = PersoneroPublicRegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('nro_celular', form.errors)
