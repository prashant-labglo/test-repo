﻿using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Xml.Linq;
using System.Net;
using PowerPoint = Microsoft.Office.Interop.PowerPoint;
using Office = Microsoft.Office.Core;
using Nancy;
using Nancy.Hosting.Self;

namespace LisaTools
{
    public partial class LisaToolsAddin
    {
        NancyHost host;
        private void ThisAddIn_Startup(object sender, System.EventArgs e)
        {
            HostConfiguration hostConfigs = new HostConfiguration();
            hostConfigs.UrlReservations.CreateAutomatically = true;

            // Create the host and start the service.
            host = new NancyHost(hostConfigs, new Uri("http://localhost:1234"));
            host.Start();
            RestApiBridge.app = this.Application;

            this.Application.PresentationNewSlide +=
                           new PowerPoint.EApplication_PresentationNewSlideEventHandler(
                           Application_PresentationNewSlide);
        }

        private void ThisAddIn_Shutdown(object sender, System.EventArgs e)
        {
            host.Stop();

            RestApiBridge.app = null;
        }

        void Application_PresentationNewSlide(PowerPoint.Slide Sld)
        {
            PowerPoint.Shape textBox = Sld.Shapes.AddTextbox(
                Office.MsoTextOrientation.msoTextOrientationHorizontal, 0, 0, 500, 50);
            textBox.TextFrame.TextRange.InsertAfter("This text was added by using code.");
        }

        #region VSTO generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InternalStartup()
        {
            this.Startup += new System.EventHandler(ThisAddIn_Startup);
            this.Shutdown += new System.EventHandler(ThisAddIn_Shutdown);
        }
        
        #endregion
    }
}
