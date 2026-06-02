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

    def test_login_confirmed_and_completed_personero_redirects_to_escrutinio(self):
        """Verifica que si un personero está confirmado y completó su perfil, vaya directo a reportar votos."""
        self.personero.perfil_completado = True
        self.personero.save()
        
        # Test login view redirect
        response = self.client.post(reverse('personeros:login'), {
            'username': '12345678',
            'password': '12345678'
        })
        self.assertRedirects(response, reverse('personeros:reportar_escrutinio'))

        # Test dashboard page redirect
        response = self.client.get(reverse('personeros:dashboard'))
        self.assertRedirects(response, reverse('personeros:reportar_escrutinio'))

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

    def test_export_selective_ids_success(self):
        """Verifica que la exportación exporte únicamente los IDs seleccionados cuando se pasa el parámetro GET 'ids'."""
        # Agregar otro personero de prueba
        p2 = Personero.objects.create(
            dni='87654321',
            nombres='Carlos',
            apellido_paterno='Pérez',
            apellido_materno='Gómez',
            nro_celular='999999999',
            estado='confirmado'
        )

        self.client.login(username='admin_test', password='password123')

        # Exportar únicamente el personero con DNI '12345678' (id de self.personero)
        response = self.client.get(reverse('personeros:exportar_excel'), {'ids': f'{self.personero.pk}'})
        csv_text = response.content[3:].decode('utf-8')

        # El primer personero debe estar presente
        self.assertIn('12345678;HERRERA;AYAY;EDUARDO', csv_text)
        # El segundo personero (a pesar de estar confirmado) NO debe estar presente
        self.assertNotIn('87654321;PÉREZ;GÓMEZ;CARLOS', csv_text)

        # Exportar ambos personeros seleccionándolos por ID
        response = self.client.get(reverse('personeros:exportar_excel'), {'ids': f'{self.personero.pk},{p2.pk}'})
        csv_text = response.content[3:].decode('utf-8')

        # Ambos deben estar presentes
        self.assertIn('12345678;HERRERA;AYAY;EDUARDO', csv_text)
        self.assertIn('87654321;PÉREZ;GÓMEZ;CARLOS', csv_text)

        # CASO CRÍTICO: Exportar por ID con un filtro de búsqueda 'q' activo que no coincide con uno de ellos.
        # Debe ignorar el filtro 'q' y exportar ambos seleccionados de todas formas.
        response = self.client.get(reverse('personeros:exportar_excel'), {'ids': f'{self.personero.pk},{p2.pk}', 'q': 'Carlos'})
        csv_text = response.content[3:].decode('utf-8')

        # Ambos deben seguir presentes ignorando el filtro 'q'
        self.assertIn('12345678;HERRERA;AYAY;EDUARDO', csv_text)
        self.assertIn('87654321;PÉREZ;GÓMEZ;CARLOS', csv_text)

    def test_export_ordering_priority(self):
        """Verifica que al exportar, los personeros de Centro de Votación (Coordinador2)
        aparecen al inicio, y los registros se ordenan de forma descendente por fecha de creación.
        """
        from datetime import timedelta
        from django.utils import timezone
        now = timezone.now()

        # Limpiar personeros creados en setUp para tener control total
        Personero.objects.all().delete()

        # Crear personeros de prueba
        p_a = Personero.objects.create(
            dni='11111111', nombres='A', apellido_paterno='A', apellido_materno='A',
            cargo='Coordinador3', estado='confirmado'
        )
        p_b = Personero.objects.create(
            dni='22222222', nombres='B', apellido_paterno='B', apellido_materno='B',
            cargo='Coordinador2', estado='confirmado'
        )
        p_c = Personero.objects.create(
            dni='33333333', nombres='C', apellido_paterno='C', apellido_materno='C',
            cargo='Coordinador2', estado='confirmado'
        )
        p_d = Personero.objects.create(
            dni='44444444', nombres='D', apellido_paterno='D', apellido_materno='D',
            cargo='Coordinador1', estado='confirmado'
        )

        # Actualizar fecha_creacion usando update() para burlar auto_now_add
        Personero.objects.filter(pk=p_a.pk).update(fecha_creacion=now - timedelta(days=2))
        Personero.objects.filter(pk=p_b.pk).update(fecha_creacion=now - timedelta(days=1))
        Personero.objects.filter(pk=p_c.pk).update(fecha_creacion=now)
        Personero.objects.filter(pk=p_d.pk).update(fecha_creacion=now - timedelta(days=3))

        self.client.login(username='admin_test', password='password123')
        response = self.client.get(reverse('personeros:exportar_excel'))
        csv_text = response.content[3:].decode('utf-8')

        # Partir las líneas del CSV (obviar cabecera y línea vacía final)
        lines = [line for line in csv_text.split('\r\n') if line.strip()][1:]

        # La primera fila debe ser Personero C (Coordinador2, Creado Hoy)
        self.assertTrue(lines[0].startswith('33333333;C;C;C'), f"Expected C first, got: {lines[0]}")
        # La segunda fila debe ser Personero B (Coordinador2, Creado Ayer)
        self.assertTrue(lines[1].startswith('22222222;B;B;B'), f"Expected B second, got: {lines[1]}")
        # La tercera fila debe ser Personero A (Coordinador3, Creado hace 2 días)
        self.assertTrue(lines[2].startswith('11111111;A;A;A'), f"Expected A third, got: {lines[2]}")
        # La cuarta fila debe ser Personero D (Coordinador1, Creado hace 3 días)
        self.assertTrue(lines[3].startswith('44444444;D;D;D'), f"Expected D fourth, got: {lines[3]}")


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


from personeros.models import ActaElectoral, CentroVotacion, Departamento, Provincia, Distrito
from personeros.forms import ActaElectoralForm

class ActaElectoralTestCase(TestCase):
    def setUp(self):
        # Setup UBIGEO
        self.dpto = Departamento.objects.create(id_ubigeo='15', nombre='LIMA')
        self.prov = Provincia.objects.create(id_ubigeo='1501', nombre='LIMA', departamento=self.dpto)
        self.dist = Distrito.objects.create(id_ubigeo='150101', nombre='LIMA', provincia=self.prov)

        # Setup local de votación
        self.local = CentroVotacion.objects.create(
            distrito=self.dist,
            nombre='COLEGIO NACIONAL GUADALUPE',
            direccion='AV. ALFONSO UGARTE 1227'
        )

        # Setup personero
        self.personero = Personero.objects.create(
            dni='87654321',
            nombres='CARLOS',
            apellido_paterno='PÉREZ',
            apellido_materno='GÓMEZ',
            nro_celular='987654321',
            distrito=self.dist,
            centro_votacion=self.local,
            numero_mesa='123456',
            estado='confirmado',
            perfil_completado=True
        )
        self.personero_user = self.personero.usuario
        self.client = Client()

    def test_acta_form_valid_with_consistent_data(self):
        """Verifica que el formulario de acta es válido cuando la suma de votos es <= 300."""
        data = {
            'numero_mesa': '123456',
            'votos_jp': 120,
            'votos_k': 110,
            'votos_blanco': 10,
            'votos_nulos': 15,
            'votos_viciados': 5,
        }
        form = ActaElectoralForm(data=data)
        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_acta_form_invalid_if_total_votos_exceeds_300(self):
        """Verifica que el formulario de acta no es válido si la suma de votos es > 300."""
        data = {
            'numero_mesa': '123456',
            'votos_jp': 160,
            'votos_k': 150, # 160 + 150 = 310 > 300
            'votos_blanco': 0,
            'votos_nulos': 0,
            'votos_viciados': 0,
        }
        form = ActaElectoralForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors) # Validación a nivel de formulario/clean

    def test_reportar_escrutinio_success(self):
        """Verifica que un personero con perfil completado y mesa asignada pueda reportar el escrutinio exitosamente."""
        self.client.force_login(self.personero_user)
        response = self.client.post(reverse('personeros:reportar_escrutinio'), {
            'numero_mesa': '123456',
            'votos_jp': 85,
            'votos_k': 75,
            'votos_blanco': 5,
            'votos_nulos': 5,
            'votos_viciados': 0,
        })
        self.assertEqual(response.status_code, 302) # Redirección tras guardar
        
        # Verificar que el acta se haya guardado con el centro y mesa del personero
        self.assertTrue(self.personero.actas.filter(numero_mesa='123456').exists())
        acta = self.personero.actas.get(numero_mesa='123456')
        self.assertEqual(acta.votos_jp, 85)
        self.assertEqual(acta.votos_k, 75)
        self.assertEqual(acta.centro_votacion, self.local)

    def test_reportar_escrutinio_gated_by_profile_completion(self):
        """Verifica que un personero con perfil incompleto no pueda reportar el escrutinio."""
        self.personero.perfil_completado = False
        self.personero.save()

        self.client.force_login(self.personero_user)
        response = self.client.post(reverse('personeros:reportar_escrutinio'), {
            'numero_mesa': '123456',
            'votos_jp': 50,
            'votos_k': 50,
        })
        self.assertEqual(response.status_code, 302)
        # No se debió crear ningún acta
        self.assertFalse(self.personero.actas.filter(numero_mesa='123456').exists())

    def test_reportar_escrutinio_double_submission_prevented(self):
        """Verifica que no se pueda reportar dos veces el escrutinio para la misma mesa."""
        # Registrar primer escrutinio
        ActaElectoral.objects.create(
            personero=self.personero,
            centro_votacion=self.local,
            numero_mesa='123456',
            votos_jp=100,
            votos_k=100
        )

        self.client.force_login(self.personero_user)
        response = self.client.post(reverse('personeros:reportar_escrutinio'), {
            'numero_mesa': '123456',
            'votos_jp': 120,
            'votos_k': 120,
        })
        # Debe retornar la vista del formulario cargando el mensaje de error (200 OK)
        self.assertEqual(response.status_code, 200)
        
        # El acta debe mantenerse intacta (votos_jp=100, no 120)
        acta = self.personero.actas.get(numero_mesa='123456')
        self.assertEqual(acta.votos_jp, 100)


from django.core.exceptions import ValidationError
from django.db import IntegrityError

class PersoneroCentroVotacionUniqueTestCase(TestCase):
    def setUp(self):
        # Setup UBIGEO
        self.dpto = Departamento.objects.create(id_ubigeo='15', nombre='LIMA')
        self.prov = Provincia.objects.create(id_ubigeo='1501', nombre='LIMA', departamento=self.dpto)
        self.dist = Distrito.objects.create(id_ubigeo='150101', nombre='LIMA', provincia=self.prov)

        # Setup local de votación
        self.local = CentroVotacion.objects.create(
            distrito=self.dist,
            nombre='COLEGIO NACIONAL GUADALUPE',
            direccion='AV. ALFONSO UGARTE 1227'
        )

    def test_create_first_personero_cv_success(self):
        """Verifica que se puede registrar exitosamente el primer Personero Centro de Votación."""
        p1 = Personero(
            dni='11111111',
            nombres='MARCO',
            apellido_paterno='DIAZ',
            apellido_materno='SILVA',
            nro_celular='999999991',
            distrito=self.dist,
            centro_votacion=self.local,
            cargo='Coordinador2',
            estado='confirmado'
        )
        p1.full_clean()
        p1.save()
        self.assertEqual(Personero.objects.count(), 1)

    def test_create_second_personero_cv_raises_validation_error(self):
        """Verifica que el método clean() lance un ValidationError al intentar registrar un duplicado activo."""
        p1 = Personero.objects.create(
            dni='11111111',
            nombres='MARCO',
            apellido_paterno='DIAZ',
            apellido_materno='SILVA',
            nro_celular='999999991',
            distrito=self.dist,
            centro_votacion=self.local,
            cargo='Coordinador2',
            estado='confirmado'
        )

        p2 = Personero(
            dni='22222222',
            nombres='LUCIA',
            apellido_paterno='ALVA',
            apellido_materno='CASTRO',
            nro_celular='999999992',
            distrito=self.dist,
            centro_votacion=self.local,
            cargo='Coordinador2',
            estado='pendiente'
        )

        with self.assertRaises(ValidationError) as ctx:
            p2.full_clean()
        
        self.assertIn('cargo', ctx.exception.error_dict)
        self.assertIn('Ya existe un "Personero Centro de Votación" activo', ctx.exception.error_dict['cargo'][0].message)

    def test_create_second_personero_cv_db_integrity_error(self):
        """Verifica que guardar un duplicado directamente sin full_clean() lance un IntegrityError en la DB."""
        Personero.objects.create(
            dni='11111111',
            nombres='MARCO',
            apellido_paterno='DIAZ',
            apellido_materno='SILVA',
            nro_celular='999999991',
            distrito=self.dist,
            centro_votacion=self.local,
            cargo='Coordinador2',
            estado='confirmado'
        )

        p2 = Personero(
            dni='22222222',
            nombres='LUCIA',
            apellido_paterno='ALVA',
            apellido_materno='CASTRO',
            nro_celular='999999992',
            distrito=self.dist,
            centro_votacion=self.local,
            cargo='Coordinador2',
            estado='pendiente'
        )

        with self.assertRaises(IntegrityError):
            p2.save()

    def test_create_second_personero_cv_succeeds_if_first_retired(self):
        """Verifica que se pueda registrar un segundo personero si el primero está retirado (inactivo)."""
        p1 = Personero.objects.create(
            dni='11111111',
            nombres='MARCO',
            apellido_paterno='DIAZ',
            apellido_materno='SILVA',
            nro_celular='999999991',
            distrito=self.dist,
            centro_votacion=self.local,
            cargo='Coordinador2',
            estado='retirado'
        )

        p2 = Personero(
            dni='22222222',
            nombres='LUCIA',
            apellido_paterno='ALVA',
            apellido_materno='CASTRO',
            nro_celular='999999992',
            distrito=self.dist,
            centro_votacion=self.local,
            cargo='Coordinador2',
            estado='confirmado'
        )
        # No debe lanzar ningún error de validación
        p2.full_clean()
        p2.save()
        self.assertEqual(Personero.objects.filter(estado='confirmado').count(), 1)

    def test_multiple_mesa_personeros_success(self):
        """Verifica que se puedan registrar múltiples Personeros de Mesa (cargo Coordinador3) en el mismo local."""
        p1 = Personero.objects.create(
            dni='11111111',
            nombres='MARCO',
            apellido_paterno='DIAZ',
            apellido_materno='SILVA',
            nro_celular='999999991',
            distrito=self.dist,
            centro_votacion=self.local,
            cargo='Coordinador3',
            estado='confirmado'
        )

        p2 = Personero(
            dni='22222222',
            nombres='LUCIA',
            apellido_paterno='ALVA',
            apellido_materno='CASTRO',
            nro_celular='999999992',
            distrito=self.dist,
            centro_votacion=self.local,
            cargo='Coordinador3',
            estado='confirmado'
        )
        p2.full_clean()
        p2.save()
        self.assertEqual(Personero.objects.filter(cargo='Coordinador3').count(), 2)


class PersoneroConsultaLocalTestCase(TestCase):
    def setUp(self):
        # Crear superadmin
        self.admin_user = User.objects.create_user(username='admin_test', password='password123')
        self.admin_profile = PerfilUsuario.objects.create(usuario=self.admin_user, rol='superadmin')

        # Crear un personero común
        self.personero_user = User.objects.create_user(username='personero_test', password='password123')
        self.personero_profile = PerfilUsuario.objects.create(usuario=self.personero_user, rol='personero')

        # Crear Ubicaciones de Callao
        from personeros.models import Departamento, Provincia, Distrito, CentroVotacion
        self.dpto = Departamento.objects.create(id_ubigeo='07', nombre='CALLAO')
        self.prov = Provincia.objects.create(id_ubigeo='0701', nombre='CALLAO', departamento=self.dpto)
        self.dist = Distrito.objects.create(id_ubigeo='070101', nombre='CALLAO', provincia=self.prov)

        # Crear Local
        self.local = CentroVotacion.objects.create(
            distrito=self.dist,
            nombre='IE JAZMINES DE OQUENDO',
            direccion='AV. OQUENDO 123',
            actas=10,
            electores=3000
        )

        # Crear Personero Zonal (Coordinador1)
        self.cz = Personero.objects.create(
            dni='11111111', nombres='MARCO', apellido_paterno='DIAZ', apellido_materno='SILVA',
            distrito=self.dist, centro_votacion=self.local, cargo='Coordinador1', estado='confirmado'
        )

        # Crear Personero de Centro (Coordinador2)
        self.pcv = Personero.objects.create(
            dni='22222222', nombres='LUCIA', apellido_paterno='ALVA', apellido_materno='CASTRO',
            distrito=self.dist, centro_votacion=self.local, cargo='Coordinador2', estado='confirmado'
        )

        # Crear Personero de Mesa (Coordinador3)
        self.pm = Personero.objects.create(
            dni='33333333', nombres='JUAN', apellido_paterno='PEREZ', apellido_materno='GOMEZ',
            distrito=self.dist, centro_votacion=self.local, cargo='Coordinador3', estado='confirmado',
            numero_mesa='081455'
        )

        self.client = Client()

    def test_consulta_local_view_access(self):
        """Verifica que un administrador pueda acceder al panel de consulta local y un personero común sea redirigido."""
        # Intento anónimo redirecciona
        response = self.client.get(reverse('personeros:consulta_local'))
        self.assertEqual(response.status_code, 302)

        # Admin accede con éxito
        self.client.login(username='admin_test', password='password123')
        response = self.client.get(reverse('personeros:consulta_local'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'personeros/consulta_local.html')

        # Personero redirecciona
        self.client.logout()
        self.client.login(username='personero_test', password='password123')
        response = self.client.get(reverse('personeros:consulta_local'))
        self.assertEqual(response.status_code, 302)

    def test_api_local_detalle_success(self):
        """Verifica que la API retorne correctamente la estructura completa del local en formato JSON."""
        self.client.login(username='admin_test', password='password123')
        response = self.client.get(reverse('personeros:api_local_detalle', kwargs={'local_id': self.local.pk}))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['local']['nombre'], 'IE JAZMINES DE OQUENDO')
        self.assertEqual(data['local']['distrito'], 'CALLAO')
        self.assertEqual(data['local']['electores'], 3000)

        # Coordinador Zonal
        self.assertEqual(len(data['coordinadores_zonales']), 1)
        self.assertEqual(data['coordinadores_zonales'][0]['nombre_completo'], 'MARCO DIAZ SILVA')

        # Personero Centro
        self.assertIsNotNone(data['personero_centro_votacion'])
        self.assertEqual(data['personero_centro_votacion']['nombre_completo'], 'LUCIA ALVA CASTRO')

        # Personero Mesa
        self.assertEqual(len(data['personeros_mesa']), 1)
        self.assertEqual(data['personeros_mesa'][0]['mesa'], '081455')
        self.assertEqual(data['personeros_mesa'][0]['nombre_completo'], 'JUAN PEREZ GOMEZ')


