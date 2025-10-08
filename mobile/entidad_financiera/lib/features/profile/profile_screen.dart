import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../auth/auth.dart';
import 'profile_controller.dart';

class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});
  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  bool editing = false;

  final telCtrl = TextEditingController();
  final dirCtrl = TextEditingController();
  final ocupCtrl = TextEditingController();
  final ingresosCtrl = TextEditingController();
  final fechaNacCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    Future.microtask(() => ref.read(profileProvider.notifier).load());
  }

  @override
  void dispose() {
    telCtrl.dispose();
    dirCtrl.dispose();
    ocupCtrl.dispose();
    ingresosCtrl.dispose();
    fechaNacCtrl.dispose();
    super.dispose();
  }

  void _fill(Map<String, dynamic>? cliente) {
    telCtrl.text = cliente?['telefono'] ?? '';
    dirCtrl.text = cliente?['direccion'] ?? '';
    ocupCtrl.text = cliente?['ocupacion'] ?? '';
    ingresosCtrl.text = cliente?['ingresos_mensuales']?.toString() ?? '';
    fechaNacCtrl.text = cliente?['fecha_nacimiento'] ?? '';
  }

  Future<void> _save() async {
    final body = {
      'telefono': telCtrl.text.trim(),
      'direccion': dirCtrl.text.trim(),
      'ocupacion': ocupCtrl.text.trim(),
      'ingresos_mensuales': ingresosCtrl.text.trim().isEmpty
          ? null
          : num.tryParse(ingresosCtrl.text.trim()),
      'fecha_nacimiento': fechaNacCtrl.text.trim().isEmpty
          ? null
          : fechaNacCtrl.text.trim(), // YYYY-MM-DD
    };
    await ref.read(profileProvider.notifier).saveCliente(body);
    if (!mounted) return;
    setState(() => editing = false);
  }

  Future<void> _refresh() => ref.read(profileProvider.notifier).load();

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authProvider);
    final st = ref.watch(profileProvider);

    final me = st.me;
    final user = me ?? auth.user; // fallback
    final cliente = me?['cliente_info'];
    final ui = me?['username'] ?? user?['username'] ?? '';
    final name = (me?['first_name'] ?? user?['first_name'] ?? '')
                 .toString()
                 .trim();
    final last = (me?['last_name'] ?? user?['last_name'] ?? '')
                 .toString()
                 .trim();
    final fullName = ([name, last]..removeWhere((e)=>e.isEmpty)).join(' ');
    final email = me?['email'] ?? user?['email'] ?? '';

    if (!editing) _fill(cliente);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Mi perfil'),
        actions: [
          IconButton(
            icon: Icon(editing ? Icons.close : Icons.edit),
            onPressed: () => setState(() => editing = !editing),
            tooltip: editing ? 'Cancelar' : 'Editar',
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Header
            Container(
              padding: const EdgeInsets.all(16),
              decoration: _card,
              child: Row(
                children: [
                  CircleAvatar(
                    radius: 28,
                    child: Text(
                      (fullName.isNotEmpty ? fullName[0] : ui.isNotEmpty ? ui[0] : '?').toUpperCase(),
                      style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(fullName.isEmpty ? ui : fullName,
                            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
                        const SizedBox(height: 2),
                        Text(email, style: const TextStyle(color: Colors.grey)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),

            // Resumen documento
            if (cliente != null) Container(
              padding: const EdgeInsets.all(16),
              decoration: _card,
              child: Wrap(
                spacing: 16,
                runSpacing: 8,
                children: [
                  _pill('Documento', '${cliente['tipo_documento'] ?? ''} ${cliente['numero_documento'] ?? ''}'.trim()),
                  _pill('Puntaje', '${cliente['puntuacion_crediticia'] ?? 0}'),
                  _pill('Preferencial', (cliente['es_cliente_preferencial'] ?? false) ? 'Sí' : 'No'),
                ],
              ),
            ),
            const SizedBox(height: 12),

            // Form cliente
            Container(
              decoration: _card,
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Datos del cliente',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                  const SizedBox(height: 10),
                  _field('Teléfono', telCtrl, enabled: editing, keyboard: TextInputType.phone),
                  _field('Dirección', dirCtrl, enabled: editing),
                  _field('Ocupación', ocupCtrl, enabled: editing),
                  _field('Ingresos mensuales', ingresosCtrl, enabled: editing, keyboard: TextInputType.number),
                  _field('Fecha nac. (YYYY-MM-DD)', fechaNacCtrl, enabled: editing, keyboard: TextInputType.datetime),
                  if (st.error != null) Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(st.error!, style: const TextStyle(color: Colors.red)),
                  ),
                  const SizedBox(height: 8),
                  if (editing)
                    FilledButton.icon(
                      onPressed: st.loading ? null : _save,
                      icon: const Icon(Icons.save),
                      label: const Text('Guardar cambios'),
                    )
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  BoxDecoration get _card => BoxDecoration(
    color: Colors.white,
    borderRadius: BorderRadius.circular(14),
    boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 8, offset: Offset(0,2))]
  );

  Widget _pill(String k, String v) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0xFFF2F5F8),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Text('$k: ', style: const TextStyle(color: Colors.black54)),
        Text(v, style: const TextStyle(fontWeight: FontWeight.w600)),
      ]),
    );
  }

  Widget _field(String label, TextEditingController c, {bool enabled=true, TextInputType? keyboard}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: TextField(
        controller: c,
        enabled: enabled,
        keyboardType: keyboard,
        decoration: InputDecoration(
          labelText: label,
          border: const OutlineInputBorder(),
          isDense: true,
        ),
      ),
    );
  }
}
