import jakarta.mail.internet.MimeMessage;
import org.springframework.core.io.ClassPathResource; // IMPORTANTE
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.mail.javamail.JavaMailSender;

@Service
public class EmailService {

    @Autowired
    private JavaMailSender mailSender;

    public void enviarNotificacion(EmailRequest request) {
        try {
            MimeMessage message = mailSender.createMimeMessage();
            // Activamos multipart (true) para poder embeber la imagen
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");

            helper.setTo(request.getDestinatario());
            
            String subject = "";
            String colorPrincipal = "#28a745"; // Verde (Aprobado por defecto)
            String mensajeCuerpo = "";
            String botonTexto = "Ir al Panel";

            // Lógica según el estado
            switch (request.getEstado().toUpperCase()) {
                case "PENDIENTE":
                    subject = "Solicitud Recibida - Red Solidaria";
                    colorPrincipal = "#ffc107"; // Amarillo
                    mensajeCuerpo = "Hemos recibido tu registro. Tu cuenta está en proceso de validación por nuestro equipo técnico.";
                    botonTexto = "Ver mi Estado";
                    break;
                case "APROBADO":
                    subject = "¡Felicidades! Tu fundación ha sido aprobada";
                    colorPrincipal = "#28a745"; // Verde
                    mensajeCuerpo = "¡Buenas noticias! Tu cuenta ha sido activada con éxito. Ya puedes acceder al panel para gestionar donaciones.";
                    break;
                case "RECHAZADO":
                    subject = "Información sobre tu solicitud";
                    colorPrincipal = "#dc3545"; // Rojo
                    mensajeCuerpo = "Lamentamos informarte que tu solicitud no pudo ser aprobada en este momento.";
                    botonTexto = "Contactar Soporte";
                    break;
            }

            helper.setSubject(subject);

            // --- DISEÑO HTML ACTUALIZADO CON LOGO EMBEBIDO ---
            String htmlContent = 
                "<div style='font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;'>" +
                    "<div style='max-width: 600px; margin: auto; background: white; border-radius: 8px; overflow: hidden; border: 1px solid #ddd;'>" +
                        
                        // CABECERA CON COLOR Y LOGO
                        "<div style='background-color: " + colorPrincipal + "; padding: 10px; text-align: center; color: white;'>" +
                            // USAMOS 'cid:logoImage' como referencia interna
                            "<img src='cid:logoImage' alt='Red Solidaria Logo' style='max-height: 80px; width: auto; border-radius: 5px; margin-bottom: 5px;'/>" +
                            "<h1 style='margin: 0; font-size: 24px;'>Red Solidaria</h1>" +
                        "</div>" +
                        
                        // CUERPO DEL MENSAJE
                        "<div style='padding: 30px; text-align: center;'>" +
                            "<h2 style='color: #333;'>Hola, " + request.getNombreFundacion() + "</h2>" +
                            "<p style='color: #666; font-size: 16px; line-height: 1.5;'>" + mensajeCuerpo + "</p>" +
                            "<br><br>" +
                            // BOTÓN DINÁMICO
                            "<a href='http://localhost:5000/login' style='background-color: " + colorPrincipal + "; color: white; padding: 15px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px; display: inline-block;'> " + botonTexto + " </a>" +
                        "</div>" +
                        
                        // PIE DE PÁGINA
                        "<div style='background-color: #eee; padding: 15px; text-align: center; font-size: 12px; color: #888;'>" +
                            "Este es un correo automático del sistema de Red Solidaria, por favor no respondas a este mensaje." +
                        "</div>" +
                    "</div>" +
                "</div>";

            helper.setText(htmlContent, true); // Es HTML

            // --- INYECCIÓN FÍSICA DE LA IMAGEN (CID) ---
            // Buscamos la imagen en src/main/resources/static/images/
            ClassPathResource image = new ClassPathResource("static/images/logo.jpeg");
            
            // "Vinculamos" el ID 'logoImage' que usamos en el HTML con el archivo real
            helper.addInline("logoImage", image);

            mailSender.send(message);
            System.out.println("✅ Correo HTML con Logo embebido enviado con éxito!");

        } catch (Exception e) {
            System.out.println("❌ Error enviando HTML con Logo: " + e.getMessage());
            e.printStackTrace(); // Ver el error completo en consola
        }
    }
}