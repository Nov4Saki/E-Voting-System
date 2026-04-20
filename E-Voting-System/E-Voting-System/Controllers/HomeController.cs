using System.Diagnostics;
using E_Voting_System.Models;
using E_Voting_System.ViewModels;
using Microsoft.AspNetCore.Mvc;

namespace E_Voting_System.Controllers
{
    public class HomeController : Controller
    {
        private readonly ILogger<HomeController> _logger;

        public HomeController(ILogger<HomeController> logger)
        {
            _logger = logger;
        }

        public IActionResult Index()
        {
            return View();
        }

        [HttpPost]
        [ValidateAntiForgeryToken]
        public IActionResult Login(LoginViewModel vm)
        {
            if (!ModelState.IsValid)
                return RedirectToAction("Index");

            // Perform login logic here (e.g., validate user credentials, save in user table its Id only and null for voting column)
            return RedirectToAction("Index", "Vote");
        }

        public IActionResult Logout()
        {
            // Perform logout logic here (e.g., clear session, cookies, etc.)
            return RedirectToAction("Index");
        }


        
        public IActionResult Privacy()
        {
            return View();
        }

        [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
        public IActionResult Error()
        {
            return View(new ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier });
        }
    }
}
