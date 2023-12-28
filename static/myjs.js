
function redirectToCorrectPage() {
    if (document.referrer.includes("/login")) {
        window.location.href = "/akun";
    } else {
        window.location.href = "/pendaftaranonline";
    }
}

function login() {
            let nama = $('#inputName').val();
            let nik = $('#inputNIK').val();
    
            $.ajax({
                url: '/login',
                method: 'POST',
                data: {
                    nama: nama,
                    nik: nik
                },
                success: function(response) {
                    if (response.result === "success") {
                        Swal.fire({
                            title: "Berhasil melakukan login!",
                            text: response.message,
                            icon: "success"
                          }).then((result) => {
                            redirectToCorrectPage();
                        });
                        document.cookie = "mytoken=" + response.token;
                    } else {
                        Swal.fire({
                            title: "Gagal melakukan login!",
                            text: response.message,
                            icon: "error"
                          });
                    }
                },
                error : function(response){
                    if (response['result'] === 'error') {
                        Swal.fire({
                            title: "Gagal melakukan login!",
                            text: response.message,
                            icon: "error"
                          }).then((result) => {
                                location.reload();
                        });
                }
            }
                
            });
}

function register() {
    let nama = $('#inputName').val();
    let nik = $('#inputNIK').val();
    let gender = $('#inputGender').val();
    let alamat = $('#inputAddress').val();


    $.ajax({
        type: 'POST',
        url: '/register',
        data: {
            nama: nama,
            nik: nik,
            gender: gender,
            alamat: alamat
        },
        success: function (response) {
            if (response['result'] === 'success') {
                Swal.fire({
                    title: "Berhasil melakukan registrasi!",
                    text: response.message,
                    icon: "success"
                  }).then((result) => {
                        window.location.href = '/login';
                });
                // window.location.href = '/login';
            } else {
                Swal.fire({
                    title: "Gagal melakukan registrasi!",
                    text: response.message,
                    icon: "error"
                  }).then((result) => {
                    location.reload();
            });
            }
        },
        error : function(response){
            if (response['result'] === 'error') {
                Swal.fire({
                    title: "Gagal melakukan registrasi!",
                    text: response.message,
                    icon: "error"
                  }).then((result) => {
                        location.reload();
                });
        }
    }
    });
}
function daftar(){
    // let nama = $('#inputName').val();
    let tanggal = $('#inputDate').val();
    let sesi = $('#inputSession').val();
    let mcu = $('#inputMCU').val();
    let nama = $('#inputNama').val();

    
    $.ajax({
        url: '/pendaftaranonline',
        method: 'POST',
        data: {
            // nama: nama,
            tanggal: tanggal,
            sesi: sesi,
            mcu: mcu,
            nama: nama
        },
        success: function(response) {
            if (response["result"] === 'success') {
                $('#nomorAntrian').text(response.nomor_antrian);
                $('#tanggal').text(response.tanggal);
                $('#hari').text(response.hari);
                $('#sesi').text(response.sesi);
                $('#jam').text(response.jam);
                $('#resultModal').modal('show');
            } else {
                Swal.fire({
                    title: "Gagal melakukan pendaftaran!",
                    text: response.message,
                    icon: "error"
                  }).then((result) => {
                    location.reload();
            });
            }
        },
        error : function(response){
            if (response['result'] === 'error') {
                Swal.fire({
                    title: "Gagal melakukan pendaftaran!",
                    text: response.message,
                    icon: "error"
                  }).then((result) => {
                        location.reload();
                });
        }
    }
    });
}

function logAdmin() {
    let nama = $('#inputName').val();
    let pass = $('#inputPass').val();

    $.ajax({
        url: '/admin/login',
        method: 'POST',
        data: {
            nama: nama,
            pass: pass
        },
        success: function(response) {
            if (response.result === "success") {
                alert('Admin Login Berhasil');
                document.cookie = "mytoken=" + response.token;
                window.location.href = "/admin";
            } else {
                alert(response["msg"]);
            }
        }
        
    });
}

$(document).ready(function(){
    // Menampilkan modal alur pendaftaran pasien ketika gambar di klik
    $('[data-target="#modalPendaftaran"]').click(function(){
        $('#modalPendaftaran').modal('show');
    });

    // Menampilkan modal alur cek hasil pemeriksaan ketika gambar di klik
    $('[data-target="#modalPemeriksaan"]').click(function(){
        $('#modalPemeriksaan').modal('show');
    });
});

function refreshPage() {
    location.reload();
}

function sign_out() {
    $.removeCookie("mytoken", { path: "/" });
    alert("Signed out!");
    window.location.href = "/";
  }

function signout() {
    $.removeCookie("mytoken", { path: "/admin" });
    alert("Signed out!");
    window.location.href = "/admin/login";
  }


function delete_mcu(id) {
        $('#deleteModal').css('display', 'block');
        $('#confirmDelete').on('click', function() {
            $.ajax({
                url: '/delete_mcu',
                type: 'POST',
                data: JSON.stringify({ _id: id }),
                contentType: 'application/json',
                success: function(response) {
                    location.reload();
                },
                error: function(error) {
                    console.log('Error:', error);
                }
            });
        });
    }

    function delete_user(id) {
        $('#deleteModal').css('display', 'block');
        $('#confirmDelete').on('click', function() {
            $.ajax({
                url: '/delete_user',
                type: 'POST',
                data: JSON.stringify({ _id: id ,
                    user_id : id}),
                contentType: 'application/json',
                success: function(response) {
                    location.reload(3800);
                    Swal.fire({
                        title: "Deleted!",
                        text: "MCU deleted successfully.",
                        icon: "success"
                      }).then((result) => {
                            
                    });
                },
                error: function(error) {
                    console.log('Error:', error);
                }
            });
        });
    }

    function delete_antrian(id) {
        $('#deleteModal').css('display', 'block');
        $('#confirmDelete').on('click', function() {
            $.ajax({
                url: '/delete_antrian',
                type: 'POST',
                data: JSON.stringify({ _id: id }),
                contentType: 'application/json',
                success: function(response) {
                    location.reload();
                },
                error: function(error) {
                    console.log('Error:', error);
                }
            });
        });
    }


    $('.close').on('click', function() {
        $('#deleteModal').css('display', 'none');
    });




// function saveData() {
//     let formData = new FormData($('#mcuForm')[0]);
    
//     $.ajax({
//         type: 'POST',
//         url: '/save_data',
//         data: formData,
//         contentType: false,
//         processData: false,
//         success: function (response) {
//             alert(response.message);

//             // Setelah alert ditampilkan, kembali ke halaman /admin/detail/mcu
            
//             window.location.href = "/admin/detail/mcu";
            
//         },
//         error: function (error) {
//             console.error('Error:', error);
//         }
//     });
// }

function saveData() {
    var formData = {
        'nama_mcu': $('#nama_mcu').val(),
        'detailrs_mcu': $('#detailrs_mcu').val()
    };

    $.ajax({
        type: 'POST',
        url: '/save_data',
        data: formData,
        dataType: 'json',
        // encode: true
    }).done(function(data) {
        alert("Data berhasil disimpan")
        window.location.href = '/admin/detail/mcu';
    });
}

function tambahData() {
    // Gantilah dengan logika untuk menambah data atau alur yang sesuai
    // Contoh: redirect ke halaman tambah data
    window.location.href = '/admin/detail/mcu/editrs';
}

function inputData() {
    window.location.href = '/admin/mcu';
}
