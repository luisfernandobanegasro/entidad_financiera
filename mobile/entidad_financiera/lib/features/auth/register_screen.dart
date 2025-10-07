// lib/features/auth/register_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/widgets/app_button.dart';
import '../../core/widgets/app_text_field.dart';
import '../../utils/validators.dart';
import 'auth_controller.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});
  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final usernameCtrl = TextEditingController();
  final emailCtrl = TextEditingController();
  final passCtrl = TextEditingController();
  String? error;
  bool _hide = true;

  @override
  void dispose() {
    usernameCtrl.dispose();
    emailCtrl.dispose();
    passCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final username = usernameCtrl.text.trim();
    final email = emailCtrl.text.trim();
    final pass = passCtrl.text;

    if (!Validators.isUsername(username)) {
      setState(() => error = 'Usuario inválido');
      return;
    }
    if (!Validators.isEmail(email)) {
      setState(() => error = 'Email inválido');
      return;
    }
    if (!Validators.minLen(pass, 6)) {
      setState(() => error = 'Contraseña muy corta (mín. 6)');
      return;
    }

    try {
      await ref
          .read(authProvider.notifier)
          .register(username: username, email: email, password: pass);
      if (!mounted) return;
      context.go('/login');
    } catch (_) {
      setState(() => error = 'No se pudo registrar');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar:
          AppBar(leading: BackButton(onPressed: () => context.go('/login'))),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text(
                    'Crear cuenta',
                    style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 18),
                  AppTextField(
                    hint: 'Usuario',
                    controller: usernameCtrl,
                    prefixIcon: Icons.person_outline,
                    onSubmitted: (_) => _submit(),
                  ),
                  const SizedBox(height: 12),
                  AppTextField(
                    hint: 'Correo electrónico',
                    controller: emailCtrl,
                    prefixIcon: Icons.email_outlined,
                    keyboardType: TextInputType.emailAddress,
                    onSubmitted: (_) => _submit(),
                  ),
                  const SizedBox(height: 12),
                  AppTextField(
                    hint: 'Contraseña',
                    controller: passCtrl,
                    obscure: _hide,
                    prefixIcon: Icons.lock_outline,
                    suffixIcon: IconButton(
                      icon: Icon(
                        _hide ? Icons.visibility_off : Icons.visibility,
                      ),
                      onPressed: () => setState(() => _hide = !_hide),
                    ),
                    onSubmitted: (_) => _submit(),
                  ),
                  const SizedBox(height: 8),
                  if (error != null)
                    Text(error!, style: const TextStyle(color: Colors.red)),
                  const Spacer(),
                  AppButton('Registrarse', onPressed: _submit),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
