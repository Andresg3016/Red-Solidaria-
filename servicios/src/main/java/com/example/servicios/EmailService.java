package com.example.servicios; 

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.ClassPathResource;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;

import jakarta.mail.internet.MimeMessage;

@Service
public class EmailService {

    @Autowired
    private JavaMailSender mailSender;

    public void enviarNotificacion(EmailRequest request) {
        try {
            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");

            helper.setTo(request.getDestinatario());
            
            String subject = "";
            String mensajeCuerpo = "";
            String botonTexto = "Ir al Panel";
            
            // --- COLORES EXTRAÍDOS DE TU CSS ---
            String colorInicio = "#1e52ff"; // Azul de tu .form-header
            String colorFin = "#63ff5e";    // Verde de tu .form-header
            String colorBoton = "#28a745";  // Verde de tu .btn-submit

            // Lógica según el estado
            switch (request.getEstado().toUpperCase()) {
                case "PENDIENTE":
                    subject = "Solicitud Recibida - Red Solidaria";
                    mensajeCuerpo = "Hemos recibido tu registro. Tu cuenta está en proceso de validación por nuestro equipo técnico.";
                    botonTexto = "Ver mi Estado";
                    break;
                case "APROBADO":
                    subject = "¡Felicidades! Tu cuenta ha sido activada";
                    mensajeCuerpo = "¡Buenas noticias! Tu cuenta ha sido activada con éxito. Ya puedes acceder al panel para gestionar donaciones.";
                    break;
                case "RECHAZADO":
                    subject = "Información sobre tu solicitud";
                    // ROJO BRILLANTE PARA EL RECHAZO (Como pediste)
                    colorInicio = "#ff0000"; 
                    colorFin = "#dc2626";
                    colorBoton = "#b91c1c";
                    mensajeCuerpo = "Lamentamos informarte que tu solicitud no pudo ser aprobada en este momento.";
                    botonTexto = "Contactar Soporte";
                    break;
            }

            helper.setSubject(subject);

            // --- DISEÑO HTML CON LOS COLORES DE TU CSS ---
            String htmlContent = 
                "<div style='font-family: \"Segoe UI\", Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f2f5; padding: 20px;'>" +
                    "<div style='max-width: 600px; margin: auto; background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.15); border: 1px solid #e1e1e1;'>" +
                        
                        // CABECERA CON EL DEGRADADO DE TU PROYECTO (Azul a Verde)
                        "<div style='background: linear-gradient(135deg, " + colorInicio + " 0%, " + colorFin + " 100%); padding: 40px; text-align: center; color: white;'>" +
                            "<img src='cid:logoImage' alt='Logo' style='max-height: 85px; background: white; padding: 10px; border-radius: 15px; margin-bottom: 15px;'/>" +
                            "<h1 style='margin: 0; font-size: 30px; font-weight: bold; text-shadow: 1px 1px 4px rgba(0,0,0,0.2);'>Red Solidaria</h1>" +
                        "</div>" +
                        
                        // CUERPO (Inspirado en tu .form-container)
                        "<div style='padding: 45px; text-align: center; background-color: #fffef5;'>" +
                            "<h2 style='color: #333; font-size: 24px; margin-bottom: 20px;'>¡Hola, " + request.getNombreFundacion() + "!</h2>" +
                            "<p style='color: #555; font-size: 17px; line-height: 1.6;'>" + mensajeCuerpo + "</p>" +
                            "<br><br>" +
                            // BOTÓN CON EL ESTILO DE TU .btn-submit
                            "<a href='http://localhost:5000/login' style='background: linear-gradient(135deg, " + colorBoton + ", #20c997); color: white; padding: 16px 35px; text-decoration: none; border-radius: 12px; font-weight: bold; font-size: 16px; display: inline-block; text-transform: uppercase; letter-spacing: 1px; box-shadow: 0 5px 20px rgba(40, 167, 69, 0.3);'> " + botonTexto + " </a>" +
                        "</div>" +
                        
                        // PIE DE PÁGINA
                        "<div style='background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 13px; color: #777; border-top: 1px solid #eee;'>" +
                            "Estás recibiendo este correo porque formas parte de la <b>Red Solidaria</b>.<br>" +
                            "© 2026 Red Solidaria - Uniendo corazones." +
                        "</div>" +
                    "</div>" +
                "</div>";

            helper.setText(htmlContent, true);

            ClassPathResource image = new ClassPathResource("static/images/logo.jpeg");
            helper.addInline("logoImage", image);

            mailSender.send(message);
            System.out.println("✅ Correo enviado con degradado exacto del proyecto!");

        } catch (Exception e) {
            System.out.println("❌ Error: " + e.getMessage());
            e.printStackTrace(); 
        }
    }
}