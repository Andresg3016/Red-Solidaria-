package com.example.servicios;

public class EmailRequest {
    private String destinatario;
    private String nombreFundacion;
    private String estado; 
    
    // --- NUEVOS CAMPOS PARA EL REPORTE ---
    private String nit;
    private int cantidadDonaciones;
    private String categoriaFiltrada;
    private String estadoFiltrado;

    // Getters y Setters de los campos originales
    public String getDestinatario() { return destinatario; }
    public void setDestinatario(String destinatario) { this.destinatario = destinatario; }
    public String getNombreFundacion() { return nombreFundacion; }
    public void setNombreFundacion(String nombreFundacion) { this.nombreFundacion = nombreFundacion; }
    public String getEstado() { return estado; }
    public void setEstado(String estado) { this.estado = estado; }

    // Getters y Setters de los nuevos campos
    public String getNit() { return nit; }
    public void setNit(String nit) { this.nit = nit; }
    public int getCantidadDonaciones() { return cantidadDonaciones; }
    public void setCantidadDonaciones(int cantidadDonaciones) { this.cantidadDonaciones = cantidadDonaciones; }
    public String getCategoriaFiltrada() { return categoriaFiltrada; }
    public void setCategoriaFiltrada(String categoriaFiltrada) { this.categoriaFiltrada = categoriaFiltrada; }
    public String getEstadoFiltrado() { return estadoFiltrado; }
    public void setEstadoFiltrado(String estadoFiltrado) { this.estadoFiltrado = estadoFiltrado; }
}