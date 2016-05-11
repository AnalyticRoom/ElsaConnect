using ElsaConnectWebApp;
using Microsoft.Owin;
using Owin;

[assembly: OwinStartup(typeof(StartUp))]

namespace ElsaConnectWebApp
{
    public class StartUp
    {
        public void Configuration(IAppBuilder app)
        {
            //app.Run(context => context.Response.WriteAsync("Blue skies from now on."));
        }
    }
}