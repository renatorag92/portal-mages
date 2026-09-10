document.addEventListener('DOMContentLoaded', function () {
    const sidebar = document.getElementById('sidebar');
  
    sidebar.addEventListener('mouseenter', function () {
      sidebar.classList.add('hover-expanded');
    });
  
    sidebar.addEventListener('mouseleave', function () {
      sidebar.classList.remove('hover-expanded');
    });
  });