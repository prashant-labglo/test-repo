using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

using PowerPoint = Microsoft.Office.Interop.PowerPoint;
using Office = Microsoft.Office.Core;
using Nancy;
using Nancy.Hosting.Self;
using Nancy.Extensions;
using System.IO;
using System.Net;

namespace LisaTools
{
    public class RestApiBridge : NancyModule
    {
        public static PowerPoint.Application app;
        public static string tempDirectory;
        public RestApiBridge()
        {
            tempDirectory = Path.Combine(Path.GetTempPath(), Path.GetRandomFileName()) + "\\";
            Directory.CreateDirectory(tempDirectory);

            Get["/"] = parameters => "RestApiBridge for ZenTools:";
            Post["/"] = parameters =>
            {
                // Get the URL.
                var url = this.Request.Body.AsString();

                // Download file in the URL.
                var filePath = tempDirectory + Path.GetFileName(url);
                var webClient = new WebClient();
                webClient.DownloadFile(url, filePath);

                var presentationObj = app.Presentations.Open(filePath);

                foreach (PowerPoint.Slide slide in presentationObj.Slides)
                {
                    slide.Copy();
                    break;
                }

                presentationObj.Close();

                return "Done";
            };
        }
    }
}
