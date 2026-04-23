using Microsoft.EntityFrameworkCore;

namespace E_Voting_System.Entities;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options)
        : base(options)
    {
    }


    public DbSet<User> Users { get; set; }


    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<User>().HasKey(u => u.Id);
        modelBuilder.Entity<User>().Property(u => u.Id)
            .ValueGeneratedNever()
            .HasMaxLength(14);
        modelBuilder.Entity<User>().Property(u => u.Vote)
            .HasColumnType("INT")
            .HasDefaultValue(0);
    }
}

